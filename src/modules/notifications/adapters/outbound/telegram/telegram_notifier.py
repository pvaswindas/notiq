import asyncio
import logging

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort


class TelegramNotifier(NotificationSenderPort):
    """Outbound adapter that sends delivery jobs through Telegram APIs."""

    def __init__(self) -> None:
        """Initialize adapter logger used for delivery telemetry."""

        self._logger = logging.getLogger(__name__)

    async def send(self, job: DeliveryJob, provider_account: ProviderAccount) -> None:
        """Send a job using Telegram provider credentials referenced by the account."""

        if provider_account.provider_key != "telegram":
            raise ValueError("telegram sender received non-telegram provider account")

        # Integrate Telegram API here using provider_account.credentials_ref lookup.
        await asyncio.sleep(0)
        self._logger.info(
            "telegram notification sent",
            extra={
                "job_id": job.job_id,
                "workspace_id": job.workspace_id,
                "destination": job.destination,
                "credentials_ref": provider_account.credentials_ref,
            },
        )
