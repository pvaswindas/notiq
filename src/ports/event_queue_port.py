from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event


class EventQueuePort(ABC):
    """Contract for enqueue/dequeue behavior in legacy event fan-out flow."""

    @abstractmethod
    async def enqueue(self, event: Event, channel: Channel) -> None:
        """Publish an event-channel pair for asynchronous processing.

        Args:
            event: Legacy event entity to process.
            channel: Channel destination for that event.

        Returns:
            None.
        """

        ...

    @abstractmethod
    async def dequeue(self) -> tuple[Event, Channel]:
        """Retrieve next queued event-channel item when queue supports pull.

        Returns:
            tuple[Event, Channel]: Next queued work item.
        """

        ...
