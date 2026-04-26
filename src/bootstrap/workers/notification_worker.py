import asyncio
import logging

from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.shared.observability.metrics_service import MetricsService
from src.shared.observability.structured_logging import log_event, log_exception


class NotificationWorker:
    """Poll due delivery jobs and execute them via the processing use case.

    Purpose:
    - Provide the long-running worker loop that converts persisted
      `delivery_jobs` into actual provider delivery attempts.

    Responsibilities:
    - Claim due jobs in bounded batches.
    - Hand each claimed job to `ProcessDeliveryJobUseCase`.
    - Keep polling behavior and lease metadata consistent across runs.

    Architectural role:
    - Runtime orchestration component that sits outside the application layer
      and delegates all business decisions to the processing use case.

    Important constraints:
    - Must not implement retry or delivery policy itself.
    - Must preserve at-least-once execution by relying on repository leasing
      rather than in-memory job ownership.
    """

    _ACTIVE_POLL_DELAY_SECONDS = 0.1

    def __init__(
        self,
        worker_id: str,
        delivery_job_repository: DeliveryJobRepositoryPort,
        process_delivery_job_use_case: ProcessDeliveryJobUseCase,
        metrics_service: MetricsService,
        batch_size: int = 50,
        poll_interval_seconds: float = 1.0,
        lease_seconds: int = 30,
    ) -> None:
        """Initialize worker dependencies and polling configuration.

        Args:
            worker_id: Stable worker identifier recorded on claimed jobs.
            delivery_job_repository: Repository responsible for claim and
                update operations on persisted jobs.
            process_delivery_job_use_case: Application use case that owns job
                execution policy and state transitions.
            batch_size: Maximum number of jobs to claim in one poll cycle.
            poll_interval_seconds: Idle wait when no jobs are available.
            lease_seconds: Claim lease duration before an in-flight job becomes
                reclaimable.

        Important:
        - Polling configuration controls runtime behavior only. Business retry
          semantics remain in `ProcessDeliveryJobUseCase`.
        """

        self._worker_id = worker_id
        self._delivery_job_repository = delivery_job_repository
        self._process_delivery_job_use_case = process_delivery_job_use_case
        self._metrics = metrics_service
        self._batch_size = batch_size
        self._poll_interval_seconds = poll_interval_seconds
        self._lease_seconds = lease_seconds
        self._logger = logging.getLogger(__name__)

    async def process_batch(self) -> int:
        """Claim one batch of due jobs and process them safely.

        This function:
        - Claims due or expired-lease jobs using repository leasing rules.
        - Processes each claimed job through the application use case.
        - Logs unexpected runtime failures without terminating the worker loop.

        Returns:
            int: Number of jobs claimed in this batch.

        Edge cases:
        - A failure while processing one job does not prevent later claimed
          jobs in the same batch from running.
        - Unexpected exceptions are logged here, but job-state policy remains
          owned by the processing use case and repository.
        """

        jobs = await self._delivery_job_repository.claim_due_jobs(
            worker_id=self._worker_id,
            limit=self._batch_size,
            lease_seconds=self._lease_seconds,
        )
        self._metrics.increment("jobs_polled")
        self._metrics.set_gauge("jobs_processed_per_cycle", len(jobs))
        if jobs:
            log_event(
                self._logger,
                logging.INFO,
                "worker_jobs_claimed",
                worker_id=self._worker_id,
                claimed_jobs=len(jobs),
            )
        else:
            self._metrics.increment("worker_idle_cycles")
            log_event(self._logger, logging.DEBUG, "worker_idle_cycle", worker_id=self._worker_id)

        for job in jobs:
            try:
                await self._process_delivery_job_use_case.execute(job)
            except Exception:
                log_exception(
                    self._logger,
                    "worker_job_unexpected_failure",
                    worker_id=self._worker_id,
                    job_id=job.job_id,
                    workspace_id=job.workspace_id,
                )
        return len(jobs)

    async def run_forever(self) -> None:
        """Run the polling loop until cancelled by the runtime.

        This function:
        - Announces worker startup configuration.
        - Repeatedly claims and processes batches.
        - Sleeps longer when idle and briefly when active to avoid tight loops.

        Returns:
            None

        Important:
        - Cancellation and process lifecycle are controlled by the runtime
          entrypoint or process manager.
        """

        log_event(
            self._logger,
            logging.INFO,
            "worker_started",
            worker_id=self._worker_id,
            batch_size=self._batch_size,
            poll_interval_seconds=self._poll_interval_seconds,
            lease_seconds=self._lease_seconds,
        )
        while True:
            processed_jobs = await self.process_batch()
            if processed_jobs == 0:
                await asyncio.sleep(self._poll_interval_seconds)
                continue
            await asyncio.sleep(self._ACTIVE_POLL_DELAY_SECONDS)
