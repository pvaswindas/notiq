from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount


class NotificationSenderPort(ABC):
    """Port for provider-specific notification delivery adapters."""

    @abstractmethod
    async def send(self, channel: Channel, provider_account: ProviderAccount, event: dict) -> None:
        """Send one notification using channel routing and provider-account credentials."""

        pass
