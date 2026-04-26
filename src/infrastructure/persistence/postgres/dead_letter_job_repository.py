from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import DeadLetterJobModel
from src.modules.notifications.domain.entities.dead_letter_job import DeadLetterJob
from src.modules.notifications.ports.dead_letter_job_repository_port import DeadLetterJobRepositoryPort


class PostgresDeadLetterJobRepository(DeadLetterJobRepositoryPort):
    """Postgres adapter for dead-letter job persistence and query."""

    async def save(self, job: DeadLetterJob) -> None:
        async with AsyncSessionLocal() as session:
            model = DeadLetterJobModel(
                dead_letter_job_id=job.dead_letter_job_id,
                original_job_id=job.original_job_id,
                workspace_id=job.workspace_id,
                channel_id=job.channel_id,
                provider_key=job.provider,
                payload=job.payload,
                failure_reason=job.failure_reason,
                failure_count=job.failure_count,
                last_attempt_at=job.last_attempt_at,
                created_at=job.created_at,
            )
            session.add(model)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                # Unique constraint on original_job_id makes DLQ insertion idempotent.
                return

    async def get_by_id(self, dead_letter_job_id: str, workspace_id: str) -> DeadLetterJob | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DeadLetterJobModel).where(
                    DeadLetterJobModel.dead_letter_job_id == dead_letter_job_id,
                    DeadLetterJobModel.workspace_id == workspace_id,
                )
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_entity(model)

    async def list_by_workspace(self, workspace_id: str, limit: int, offset: int) -> list[DeadLetterJob]:
        capped_limit = max(1, min(limit, 500))
        capped_offset = max(0, offset)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DeadLetterJobModel)
                .where(DeadLetterJobModel.workspace_id == workspace_id)
                .order_by(desc(DeadLetterJobModel.created_at))
                .limit(capped_limit)
                .offset(capped_offset)
            )
            return [self._to_entity(model) for model in result.scalars().all()]

    @staticmethod
    def _to_entity(model: DeadLetterJobModel) -> DeadLetterJob:
        created_at = model.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        last_attempt_at = model.last_attempt_at
        if last_attempt_at.tzinfo is None:
            last_attempt_at = last_attempt_at.replace(tzinfo=timezone.utc)
        return DeadLetterJob(
            dead_letter_job_id=model.dead_letter_job_id,
            original_job_id=model.original_job_id,
            workspace_id=model.workspace_id,
            channel_id=model.channel_id,
            provider=model.provider_key,
            payload=dict(model.payload or {}),
            failure_reason=model.failure_reason,
            failure_count=model.failure_count,
            last_attempt_at=last_attempt_at,
            created_at=created_at,
        )

