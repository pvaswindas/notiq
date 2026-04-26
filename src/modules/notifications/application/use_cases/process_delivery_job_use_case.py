import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import httpx

from src.bootstrap.settings import Settings
from src.modules.notifications.application.services.delivery_safety_service import (
    DeliveryRateLimitResult,
    DeliverySafetyService,
)
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.dead_letter_job import DeadLetterJob
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.ports.dead_letter_job_repository_port import DeadLetterJobRepositoryPort
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class ProcessDeliveryJobUseCase:
    """Execute a claimed delivery job and persist lifecycle state transitions."""

    def __init__(
        self,
        sender_registry: SenderRegistryPort,
        provider_account_repository: ProviderAccountRepositoryPort,
        delivery_job_repository: DeliveryJobRepositoryPort,
        dead_letter_job_repository: DeadLetterJobRepositoryPort,
        delivery_safety_service: DeliverySafetyService,
        settings: Settings,
        id_generator: IdGeneratorPort,
    ) -> None:
        """Initialize dependencies for sender resolution, account lookup, and updates."""

        self._sender_registry = sender_registry
        self._provider_account_repository = provider_account_repository
        self._delivery_job_repository = delivery_job_repository
        self._dead_letter_job_repository = dead_letter_job_repository
        self._delivery_safety_service = delivery_safety_service
        self._settings = settings
        self._id_generator = id_generator
        self._logger = logging.getLogger(__name__)

    async def execute(self, job: DeliveryJob) -> None:
        """Process one delivery job with retry classification and status persistence.

        Flow:
        - Load and validate provider account.
        - Resolve sender by provider key and attempt delivery.
        - Mark success, retry with exponential backoff, or fail permanently.
        """

        try:
            if job.provider_account_id is None:
                raise ValueError(f"job {job.job_id} has no provider account")

            provider_account = await self._provider_account_repository.get_by_id(job.provider_account_id)
            if provider_account is None or not provider_account.is_active:
                raise ValueError(f"provider account unavailable: {job.provider_account_id}")
            if provider_account.workspace_id != job.workspace_id:
                raise ValueError(
                    f"provider account {job.provider_account_id} does not belong to workspace {job.workspace_id}"
                )
            if provider_account.provider_key != job.provider_key:
                raise ValueError(
                    f"provider account {job.provider_account_id} does not match provider {job.provider_key}"
                )

            rate_limit_result = await self._delivery_safety_service.check_rate_limit(job)
            if not rate_limit_result.allowed:
                await self._defer_rate_limited_job(job=job, rate_limit_result=rate_limit_result)
                return

            sender = self._sender_registry.resolve(job.provider_key)
            await sender.send(
                channel=Channel(
                    channel_id=job.channel_id,
                    workspace_id=job.workspace_id,
                    provider_key=job.provider_key,
                    destination=job.destination,
                    provider_account_id=job.provider_account_id,
                ),
                provider_account=provider_account,
                event=dict(job.event_payload),
            )

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
            await self._capture_dead_letter(job=job, exc=exc)
            self._logger.error(
                "notification job failed",
                extra={"job_id": job.job_id, "workspace_id": job.workspace_id, "error": failed_job.last_error},
            )

    async def _capture_dead_letter(self, job: DeliveryJob, exc: Exception) -> None:
        """Persist a DLQ entry for a job that has reached terminal failure.

        This is best-effort and must not interrupt the worker's lifecycle
        updates (FAILED status is the system-of-record signal).
        """

        reason = self._format_failure_reason(exc)
        now = datetime.now(timezone.utc)
        dead_letter = DeadLetterJob(
            dead_letter_job_id=self._id_generator.new_id(),
            original_job_id=job.job_id,
            workspace_id=job.workspace_id,
            channel_id=job.channel_id,
            provider=job.provider_key,
            payload=dict(job.event_payload),
            failure_reason=self._truncate_failure_reason(reason),
            failure_count=max(1, job.retry_count + 1),
            last_attempt_at=now,
            created_at=now,
        )
        try:
            await self._dead_letter_job_repository.save(dead_letter)
            self._logger.error(
                "dead letter job captured",
                extra={
                    "dead_letter_job_id": dead_letter.dead_letter_job_id,
                    "original_job_id": dead_letter.original_job_id,
                    "workspace_id": dead_letter.workspace_id,
                    "channel_id": dead_letter.channel_id,
                    "provider": dead_letter.provider,
                    "failure_count": dead_letter.failure_count,
                },
            )
        except Exception as capture_exc:
            self._logger.exception(
                "failed to capture dead letter job",
                extra={"job_id": job.job_id, "workspace_id": job.workspace_id, "error": str(capture_exc)},
            )

    async def _defer_rate_limited_job(self, job: DeliveryJob, rate_limit_result: DeliveryRateLimitResult) -> None:
        """Defer a job when delivery safety policy rejects the current attempt."""

        next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=self._settings.delivery_rate_limit_backoff_seconds)
        deferred_job = replace(
            job,
            status=DeliveryJobStatus.PENDING,
            last_error=self._truncate_error(
                "rate limit exceeded"
                f" scope={rate_limit_result.violated_scope}"
                f" key={rate_limit_result.violated_key}"
                f" limit={rate_limit_result.limit}"
                f" window_seconds={rate_limit_result.window_seconds}"
            ),
            processing_owner=None,
            processing_expires_at=None,
            next_retry_at=next_retry_at,
        )
        await self._delivery_job_repository.update(deferred_job)
        self._logger.warning(
            "notification job deferred by rate limit",
            extra={
                "job_id": job.job_id,
                "workspace_id": job.workspace_id,
                "channel_id": job.channel_id,
                "provider_key": job.provider_key,
                "violated_scope": rate_limit_result.violated_scope,
                "violated_key": rate_limit_result.violated_key,
                "next_retry_at": next_retry_at.isoformat(),
            },
        )

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        """Return whether an exception is retryable by infrastructure policy."""

        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code == 429 or exc.response.status_code >= 500
        if isinstance(exc, httpx.RequestError):
            return True
        return isinstance(exc, (TimeoutError, ConnectionError, OSError))

    @staticmethod
    def _truncate_error(error: str) -> str:
        """Trim stored error text to fit persistence limits and log safety."""

        if len(error) <= 1024:
            return error
        return f"{error[:1021]}..."

    @staticmethod
    def _truncate_failure_reason(error: str) -> str:
        if len(error) <= 4096:
            return error
        return f"{error[:4093]}..."

    @staticmethod
    def _format_failure_reason(exc: Exception) -> str:
        """Create a provider-aware failure reason string for DLQ storage."""

        base = f"{exc.__class__.__name__}: {exc}"
        if isinstance(exc, httpx.HTTPStatusError):
            status = getattr(exc.response, "status_code", None)
            try:
                body = exc.response.text
            except Exception:
                body = ""
            body = body.strip()
            if body:
                body = body[:2048]
                return f"{base} (status_code={status}, response_body={body})"
            return f"{base} (status_code={status})"
        return base
