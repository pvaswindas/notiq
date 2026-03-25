import asyncio

from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class TelegramNotifier(NotificationSenderPort):
    """
    Purpose:
    - Implement Telegram provider delivery adapter.

    Responsibilities:
    - Send prepared messages to Telegram destinations.

    Inputs:
    - DeliveryJob

    Outputs:
    - None

    Constraints:
    - Must not contain routing or repository logic.
    """

    async def send(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Deliver a message to Telegram destination.

        Responsibilities:
        - Simulate asynchronous provider call for outbound delivery.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Expects provider-specific destination in job.destination.
        """

        await asyncio.sleep(0)
