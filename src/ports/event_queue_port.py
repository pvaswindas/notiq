from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event


class EventQueuePort(ABC):
    @abstractmethod
    async def enqueue(self, event: Event, channel: Channel) -> None:
        ...

    @abstractmethod
    async def dequeue(self) -> tuple[Event, Channel]:
        ...
