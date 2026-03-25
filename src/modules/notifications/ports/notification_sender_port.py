from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class NotificationSenderPort(ABC):
    """
    Purpose:
    - Define outbound contract for provider-specific message delivery.

    Responsibilities:
    - Send a prepared delivery job through an external provider.

    Inputs:
    - DeliveryJob

    Outputs:
    - None

    Constraints:
    - Implementations must not mutate domain job state.
    """

    @abstractmethod
    async def send(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Deliver a prepared message to a provider destination.

        Responsibilities:
        - Execute provider API call for the given job.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Should raise an exception on delivery failure.
        """
