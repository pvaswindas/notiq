from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event


class NotificationProviderPort(ABC):
    @abstractmethod
    async def send(self, channel: Channel, event: Event) -> None:
        ...
