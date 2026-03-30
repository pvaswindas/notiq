from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event


class NotificationProviderPort(ABC):
    """Contract for legacy provider adapters used by Celery task flow."""

    @abstractmethod
    async def send(self, channel: Channel, event: Event) -> None:
        """Send one event to one channel destination.

        Args:
            channel: Target channel configuration containing provider details.
            event: Event payload to deliver.

        Returns:
            None.
        """

        ...
