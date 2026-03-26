import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class ProcessDeliveryJobUseCase:
    """
    Purpose:
    - Orchestrate provider dispatch for a single delivery job.

    Responsibilities:
    - Transition lifecycle status.
    - Resolve sender and delegate send.
    - Apply retry policy for transient failures.
    - Persist lifecycle updates.

    Constraints:
    - Must not pull jobs directly.
    """

    def __init__(
        self,
        sender_registry: SenderRegistryPort,
        delivery_job_repository: DeliveryJobRepositoryPort,
    ) -> None:
        self._sender_registry = sender_registry
        self._delivery_job_repository = delivery_job_repository
        self._logger = logging.getLogger(__name__)

    async def execute(self, job: DeliveryJob) -> None:
        processing_job = replace(
            job,
            status=DeliveryJobStatus.PROCESSING,
            last_error=None,
            next_retry_at=None,
        )
        await self._delivery_job_repository.update(processing_job)
        self._logger.info(
            "notification job started",
            extra={"job_id": job.job_id, "workspace_id": job.workspace_id, "channel_id": job.channel_id},
        )

        try:
            sender = self._sender_registry.resolve(processing_job.provider_key)
            await sender.send(processing_job)
        except Exception as exc:
            if self._is_transient_error(exc) and processing_job.retry_count < processing_job.max_retries:
                next_retry_count = processing_job.retry_count + 1
                next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=2**next_retry_count)
                retry_job = replace(
                    processing_job,
                    status=DeliveryJobStatus.PENDING,
                    retry_count=next_retry_count,
                    last_error=self._truncate_error(str(exc)),
                    next_retry_at=next_retry_at,
                )
                await self._delivery_job_repository.update(retry_job)
                self._logger.warning(
                    "notification job scheduled for retry",
                    extra={
                        "job_id": retry_job.job_id,
                        "workspace_id": retry_job.workspace_id,
                        "retry_count": retry_job.retry_count,
                        "next_retry_at": retry_job.next_retry_at.isoformat(),
                        "error": retry_job.last_error,
                    },
                )
                return

            failed_job = replace(
                processing_job,
                status=DeliveryJobStatus.FAILED,
                retry_count=min(processing_job.retry_count + 1, processing_job.max_retries),
                last_error=self._truncate_error(str(exc)),
                next_retry_at=None,
            )
            await self._delivery_job_repository.update(failed_job)
            self._logger.error(
                "notification job failed",
                extra={
                    "job_id": failed_job.job_id,
                    "workspace_id": failed_job.workspace_id,
                    "retry_count": failed_job.retry_count,
                    "error": failed_job.last_error,
                },
            )
            return

        success_job = replace(
            processing_job,
            status=DeliveryJobStatus.SUCCESS,
            last_error=None,
            next_retry_at=None,
        )
        await self._delivery_job_repository.update(success_job)
        self._logger.info(
            "notification job succeeded",
            extra={
                "job_id": success_job.job_id,
                "workspace_id": success_job.workspace_id,
                "channel_id": success_job.channel_id,
            },
        )

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        return isinstance(exc, (TimeoutError, ConnectionError, OSError))

    @staticmethod
    def _truncate_error(error: str) -> str:
        if len(error) <= 1024:
            return error
        return f"{error[:1021]}..."
