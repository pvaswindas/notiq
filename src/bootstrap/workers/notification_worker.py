import asyncio
import logging

from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort


class NotificationWorker:
    """
    Purpose:
    - Run asynchronous pull-based processing for notification delivery.

    Responsibilities:
    - Poll pending jobs from DeliveryJobRepositoryPort.
    - Process jobs in bounded batches.
    - Sleep between polling iterations to avoid tight loops.

    Constraints:
    - Must use dependency injection and avoid infrastructure construction.
    """

    def __init__(
        self,
        delivery_job_repository: DeliveryJobRepositoryPort,
        process_delivery_job_use_case: ProcessDeliveryJobUseCase,
        batch_size: int = 50,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self._delivery_job_repository = delivery_job_repository
        self._process_delivery_job_use_case = process_delivery_job_use_case
        self._batch_size = batch_size
        self._poll_interval_seconds = poll_interval_seconds
        self._logger = logging.getLogger(__name__)

    async def process_batch(self) -> int:
        jobs = await self._delivery_job_repository.get_pending_jobs(limit=self._batch_size)
        for job in jobs:
            try:
                await self._process_delivery_job_use_case.execute(job)
            except Exception:
                self._logger.exception(
                    "unexpected worker failure while processing notification job",
                    extra={"job_id": job.job_id, "workspace_id": job.workspace_id},
                )
        return len(jobs)

    async def run_forever(self) -> None:
        while True:
            await self.process_batch()
            await asyncio.sleep(self._poll_interval_seconds)
