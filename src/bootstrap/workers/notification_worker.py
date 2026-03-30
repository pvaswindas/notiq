import asyncio
import logging

from src.application.services.notification_dispatcher import NotificationDispatcher
from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.ports.event_queue_port import EventQueuePort


class NotificationWorker:
    """Poll due delivery jobs and execute them via the processing use case."""

    def __init__(
        self,
        worker_id: str,
        delivery_job_repository: DeliveryJobRepositoryPort,
        process_delivery_job_use_case: ProcessDeliveryJobUseCase,
        batch_size: int = 50,
        poll_interval_seconds: float = 1.0,
        lease_seconds: int = 30,
    ) -> None:
        self._worker_id = worker_id
        self._delivery_job_repository = delivery_job_repository
        self._process_delivery_job_use_case = process_delivery_job_use_case
        self._batch_size = batch_size
        self._poll_interval_seconds = poll_interval_seconds
        self._lease_seconds = lease_seconds
        self._logger = logging.getLogger(__name__)

    async def process_batch(self) -> int:
        jobs = await self._delivery_job_repository.claim_due_jobs(
            worker_id=self._worker_id,
            limit=self._batch_size,
            lease_seconds=self._lease_seconds,
        )
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


class EventQueueNotificationWorker:
    def __init__(
        self,
        event_queue: EventQueuePort,
        dispatcher: NotificationDispatcher,
        dequeue_timeout_seconds: float = 1.0,
    ) -> None:
        self._event_queue = event_queue
        self._dispatcher = dispatcher
        self._dequeue_timeout_seconds = dequeue_timeout_seconds
        self._stop_event = asyncio.Event()

    async def run_forever(self) -> None:
        while not self._stop_event.is_set():
            try:
                event, channel = await asyncio.wait_for(
                    self._event_queue.dequeue(),
                    timeout=self._dequeue_timeout_seconds,
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"worker dequeue error: {exc}")
                continue

            try:
                await self._dispatcher.dispatch(event=event, channel=channel)
            except Exception as exc:
                print(f"worker dispatch error provider={channel.provider}: {exc}")

    def shutdown(self) -> None:
        self._stop_event.set()
