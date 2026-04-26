import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.ports.dead_letter_job_repository_port import DeadLetterJobRepositoryPort
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort


@dataclass(slots=True, frozen=True)
class ReplayDeadLetterJobCommand:
    dead_letter_job_id: str
    workspace_id: str


@dataclass(slots=True, frozen=True)
class ReplayDeadLetterJobResult:
    delivery_job_id: str


class ReplayDeadLetterJobUseCase:
    """Re-enqueue a new delivery job from a DLQ entry (idempotent per DLQ id)."""

    def __init__(
        self,
        dead_letter_job_repository: DeadLetterJobRepositoryPort,
        delivery_job_repository: DeliveryJobRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._dead_letter_job_repository = dead_letter_job_repository
        self._delivery_job_repository = delivery_job_repository
        self._id_generator = id_generator
        self._logger = logging.getLogger(__name__)

    async def execute(self, command: ReplayDeadLetterJobCommand) -> ReplayDeadLetterJobResult:
        if not command.dead_letter_job_id:
            raise ValueError("dead_letter_job_id is required")
        if not command.workspace_id:
            raise ValueError("workspace_id is required")

        dead_letter = await self._dead_letter_job_repository.get_by_id(
            dead_letter_job_id=command.dead_letter_job_id,
            workspace_id=command.workspace_id,
        )
        if dead_letter is None:
            raise LookupError(f"dead letter job not found: {command.dead_letter_job_id}")

        original_job = await self._delivery_job_repository.get_by_id(dead_letter.original_job_id)
        if original_job is None:
            raise LookupError(f"original delivery job not found: {dead_letter.original_job_id}")
        if original_job.workspace_id != command.workspace_id:
            raise PermissionError("workspace access denied")

        replay_dedupe_key = f"dlq-replay:{dead_letter.dead_letter_job_id}"
        existing = await self._delivery_job_repository.get_by_dedupe_key(replay_dedupe_key)
        if existing is not None:
            self._logger.info(
                "dead letter replay already enqueued",
                extra={
                    "dead_letter_job_id": dead_letter.dead_letter_job_id,
                    "workspace_id": command.workspace_id,
                    "delivery_job_id": existing.job_id,
                },
            )
            return ReplayDeadLetterJobResult(delivery_job_id=existing.job_id)

        now = datetime.now(timezone.utc)
        replay_job = DeliveryJob(
            job_id=self._id_generator.new_id(),
            workspace_id=original_job.workspace_id,
            channel_id=original_job.channel_id,
            provider_key=original_job.provider_key,
            provider_account_id=original_job.provider_account_id,
            destination=original_job.destination,
            message=original_job.message,
            event_payload=dict(original_job.event_payload),
            dedupe_key=replay_dedupe_key,
            status=DeliveryJobStatus.PENDING,
            retry_count=0,
            max_retries=original_job.max_retries,
            processing_owner=None,
            processing_expires_at=None,
            last_error=None,
            next_retry_at=None,
            created_at=now,
        )

        try:
            await self._delivery_job_repository.save(replay_job)
        except Exception:
            existing_after_race = await self._delivery_job_repository.get_by_dedupe_key(replay_dedupe_key)
            if existing_after_race is not None:
                return ReplayDeadLetterJobResult(delivery_job_id=existing_after_race.job_id)
            raise

        self._logger.warning(
            "dead letter replay enqueued",
            extra={
                "dead_letter_job_id": dead_letter.dead_letter_job_id,
                "original_job_id": dead_letter.original_job_id,
                "workspace_id": command.workspace_id,
                "delivery_job_id": replay_job.job_id,
                "channel_id": replay_job.channel_id,
                "provider": replay_job.provider_key,
            },
        )

        return ReplayDeadLetterJobResult(delivery_job_id=replay_job.job_id)

