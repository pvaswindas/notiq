from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class EventQueuePort(ABC):
    """
    Purpose:
    - Define queue contract for asynchronous delivery jobs.

    Responsibilities:
    - Enqueue and dequeue delivery jobs for worker processing.

    Inputs:
    - DeliveryJob

    Outputs:
    - None or DeliveryJob depending on operation.

    Constraints:
    - Implementations must be asynchronous and non-blocking.
    """

    @abstractmethod
    async def enqueue(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Push a delivery job to queue.

        Responsibilities:
        - Persist or buffer work for asynchronous worker execution.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Must preserve job integrity.
        """

    @abstractmethod
    async def dequeue(self) -> DeliveryJob:
        """
        Purpose:
        - Pull next delivery job from queue.

        Responsibilities:
        - Return next available job for processing.

        Inputs:
        - None.

        Outputs:
        - DeliveryJob

        Constraints:
        - May await until an item becomes available.
        """

    @abstractmethod
    async def requeue(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Reinsert a job for retry processing.

        Responsibilities:
        - Preserve retry attempt state and requeue job.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Must avoid blocking semantics.
        """
