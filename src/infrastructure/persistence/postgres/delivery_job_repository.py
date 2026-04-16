from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import DeliveryJobModel
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort


class PostgresDeliveryJobRepository(DeliveryJobRepositoryPort):
    """Postgres adapter for durable delivery-job lifecycle persistence."""

    async def save(self, job: DeliveryJob) -> None:
        """Persist a new delivery job row."""

        async with AsyncSessionLocal() as session:
            model = DeliveryJobModel(
                job_id=job.job_id,
                workspace_id=job.workspace_id,
                channel_id=job.channel_id,
                provider_key=job.provider_key,
                provider_account_id=job.provider_account_id,
                destination=job.destination,
                message=job.message,
                event_payload=job.event_payload,
                dedupe_key=job.dedupe_key,
                status=job.status.value,
                retry_count=job.retry_count,
                max_retries=job.max_retries,
                next_retry_at=job.next_retry_at,
                processing_owner=job.processing_owner,
                processing_expires_at=job.processing_expires_at,
                last_error=job.last_error,
                created_at=job.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()

    async def update(self, job: DeliveryJob) -> None:
        """Persist updates for an existing delivery job row."""

        async with AsyncSessionLocal() as session:
            model = await session.get(DeliveryJobModel, job.job_id)
            if model is None:
                raise ValueError(f"delivery job not found: {job.job_id}")

            model.status = job.status.value
            model.retry_count = job.retry_count
            model.max_retries = job.max_retries
            model.next_retry_at = job.next_retry_at
            model.processing_owner = job.processing_owner
            model.processing_expires_at = job.processing_expires_at
            model.last_error = job.last_error
            model.provider_account_id = job.provider_account_id
            model.updated_at = datetime.now(timezone.utc)
            await session.commit()

    async def claim_due_jobs(self, worker_id: str, limit: int, lease_seconds: int) -> list[DeliveryJob]:
        """Atomically claim due or expired-processing jobs for a worker lease."""

        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(seconds=lease_seconds)

        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(DeliveryJobModel)
                    .where(
                        or_(
                            and_(
                                DeliveryJobModel.status == DeliveryJobStatus.PENDING.value,
                                or_(
                                    DeliveryJobModel.next_retry_at.is_(None),
                                    DeliveryJobModel.next_retry_at <= now,
                                ),
                            ),
                            and_(
                                DeliveryJobModel.status == DeliveryJobStatus.PROCESSING.value,
                                DeliveryJobModel.processing_expires_at.is_not(None),
                                DeliveryJobModel.processing_expires_at <= now,
                            ),
                        )
                    )
                    .order_by(DeliveryJobModel.created_at)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
                models = result.scalars().all()

                claimed_jobs: list[DeliveryJob] = []
                for model in models:
                    model.status = DeliveryJobStatus.PROCESSING.value
                    model.processing_owner = worker_id
                    model.processing_expires_at = lease_until
                    model.updated_at = now
                    claimed_jobs.append(self._to_entity(model))

            await session.commit()
            return claimed_jobs

    @staticmethod
    def _to_entity(model: DeliveryJobModel) -> DeliveryJob:
        """Convert ORM model into immutable domain `DeliveryJob` entity."""

        return DeliveryJob(
            job_id=model.job_id,
            workspace_id=model.workspace_id,
            channel_id=model.channel_id,
            provider_key=model.provider_key,
            provider_account_id=model.provider_account_id,
            destination=model.destination,
            message=model.message,
            event_payload=dict(model.event_payload or {}),
            dedupe_key=model.dedupe_key,
            status=DeliveryJobStatus(model.status),
            retry_count=model.retry_count,
            max_retries=model.max_retries,
            processing_owner=model.processing_owner,
            processing_expires_at=model.processing_expires_at,
            last_error=model.last_error,
            next_retry_at=model.next_retry_at,
            created_at=model.created_at,
        )
