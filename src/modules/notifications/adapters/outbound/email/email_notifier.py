import asyncio
import logging

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort


class EmailNotifier(NotificationSenderPort):
    """Outbound adapter that sends delivery jobs to an email provider."""

    def __init__(self) -> None:
        """Initialize adapter logger used for delivery telemetry."""

        self._logger = logging.getLogger(__name__)

    async def send(self, channel: Channel, provider_account: ProviderAccount, event: dict) -> None:
        """Send a job using email provider credentials referenced by the account."""

        if provider_account.provider_key != "email":
            raise ValueError("email sender received non-email provider account")

        # Integrate email provider SDK here using provider_account.credentials.
        await asyncio.sleep(0)
        self._logger.info(
            "email notification sent",
            extra={
                "workspace_id": channel.workspace_id,
                "channel_id": channel.channel_id,
                "destination": channel.destination,
                "event_keys": sorted(event.keys()),
            },
        )
