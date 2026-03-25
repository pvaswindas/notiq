import asyncio

from src.modules.notifications.ports.event_queue_port import EventQueuePort
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class InMemoryEventQueue(EventQueuePort):
    """
    Purpose:
    - Provide asynchronous in-memory queue adapter for delivery jobs.

    Responsibilities:
    - Buffer jobs for worker consumption.
    - Support retry requeue flow.

    Inputs:
    - DeliveryJob on enqueue/requeue.

    Outputs:
    - DeliveryJob on dequeue.

    Constraints:
    - Intended for local development and testing scenarios.
    """

    def __init__(self) -> None:
        """
        Purpose:
        - Initialize in-memory async queue.

        Responsibilities:
        - Create queue instance for job buffering.

        Inputs:
        - None.

        Outputs:
        - None

        Constraints:
        - Queue state is process-local.
        """

        self._queue: asyncio.Queue[DeliveryJob] = asyncio.Queue()

    async def enqueue(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Push new job onto queue.

        Responsibilities:
        - Add job to async queue without blocking caller thread.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Preserves original job content.
        """

        await self._queue.put(job)

    async def dequeue(self) -> DeliveryJob:
        """
        Purpose:
        - Retrieve next job from queue.

        Responsibilities:
        - Await and return next available job.

        Inputs:
        - None.

        Outputs:
        - DeliveryJob

        Constraints:
        - May suspend coroutine until a job exists.
        """

        return await self._queue.get()

    async def requeue(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Reinsert failed job for retry.

        Responsibilities:
        - Place updated retry job back into queue.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Caller must manage max retry boundaries.
        """

        await self._queue.put(job)
