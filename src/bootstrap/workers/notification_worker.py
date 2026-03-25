import asyncio
from dataclasses import replace

from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.ports.event_queue_port import EventQueuePort


class NotificationWorker:
    """
    Purpose:
    - Run asynchronous queue consumption for notification delivery.

    Responsibilities:
    - Pull jobs from EventQueuePort.
    - Delegate delivery to ProcessDeliveryJobUseCase.
    - Retry failed deliveries with basic exponential backoff.

    Inputs:
    - event_queue: EventQueuePort
    - process_delivery_job_use_case: ProcessDeliveryJobUseCase

    Outputs:
    - None

    Constraints:
    - Must use dependency injection and avoid infrastructure construction.
    """

    def __init__(self, event_queue: EventQueuePort, process_delivery_job_use_case: ProcessDeliveryJobUseCase) -> None:
        """
        Purpose:
        - Construct worker with injected queue port and delivery use case.

        Responsibilities:
        - Store collaborators for processing loop.

        Inputs:
        - event_queue: EventQueuePort
        - process_delivery_job_use_case: ProcessDeliveryJobUseCase

        Outputs:
        - None

        Constraints:
        - Dependencies must remain abstractions or application components.
        """

        self._event_queue = event_queue
        self._process_delivery_job_use_case = process_delivery_job_use_case

    async def process_next(self) -> None:
        """
        Purpose:
        - Process a single queued delivery job.

        Responsibilities:
        - Dequeue one job.
        - Invoke delivery orchestration.
        - Requeue failures with bounded exponential backoff.

        Inputs:
        - None.

        Outputs:
        - None

        Constraints:
        - Retry count cannot exceed job.max_attempts.
        """

        job = await self._event_queue.dequeue()
        try:
            await self._process_delivery_job_use_case.execute(job)
        except Exception:
            next_attempt = job.attempt + 1
            if next_attempt < job.max_attempts:
                backoff_seconds = min(2 ** next_attempt, 30)
                await asyncio.sleep(backoff_seconds)
                await self._event_queue.requeue(replace(job, attempt=next_attempt))

    async def run_forever(self) -> None:
        """
        Purpose:
        - Continuously process notification jobs.

        Responsibilities:
        - Execute one-job processing inside an infinite async loop.

        Inputs:
        - None.

        Outputs:
        - None

        Constraints:
        - Intended for managed bootstrap lifecycle.
        """

        while True:
            await self.process_next()
