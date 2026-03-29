import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class ProcessDeliveryJobUseCase:
    def __init__(
        self,
        sender_registry: SenderRegistryPort,
        provider_account_repository: ProviderAccountRepositoryPort,
        delivery_job_repository: DeliveryJobRepositoryPort,
    ) -> None:
        self._sender_registry = sender_registry
        self._provider_account_repository = provider_account_repository
        self._delivery_job_repository = delivery_job_repository
        self._logger = logging.getLogger(__name__)

    async def execute(self, job: DeliveryJob) -> None:
        try:
            if job.provider_account_id is None:
                raise ValueError(f"job {job.job_id} has no provider account")

            provider_account = await self._provider_account_repository.get_by_id(job.provider_account_id)
            if provider_account is None or not provider_account.is_active:
                raise ValueError(f"provider account unavailable: {job.provider_account_id}")

            sender = self._sender_registry.resolve(job.provider_key)
            await sender.send(job, provider_account)

            success_job = replace(
                job,
                status=DeliveryJobStatus.SUCCESS,
                last_error=None,
                processing_owner=None,
                processing_expires_at=None,
                next_retry_at=None,
            )
            await self._delivery_job_repository.update(success_job)
            return
        except Exception as exc:
            if self._is_transient_error(exc) and job.retry_count < job.max_retries:
                next_retry_count = job.retry_count + 1
                next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=2**next_retry_count)
                retry_job = replace(
                    job,
                    status=DeliveryJobStatus.PENDING,
                    retry_count=next_retry_count,
                    next_retry_at=next_retry_at,
                    last_error=self._truncate_error(str(exc)),
                    processing_owner=None,
                    processing_expires_at=None,
                )
                await self._delivery_job_repository.update(retry_job)
                return

            failed_job = replace(
                job,
                status=DeliveryJobStatus.FAILED,
                retry_count=min(job.retry_count + 1, job.max_retries),
                last_error=self._truncate_error(str(exc)),
                processing_owner=None,
                processing_expires_at=None,
                next_retry_at=None,
            )
            await self._delivery_job_repository.update(failed_job)
            self._logger.error(
                "notification job failed",
                extra={"job_id": job.job_id, "workspace_id": job.workspace_id, "error": failed_job.last_error},
            )

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        return isinstance(exc, (TimeoutError, ConnectionError, OSError))

    @staticmethod
    def _truncate_error(error: str) -> str:
        if len(error) <= 1024:
            return error
        return f"{error[:1021]}..."
