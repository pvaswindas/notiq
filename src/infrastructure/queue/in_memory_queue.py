import asyncio

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.ports.event_queue_port import EventQueuePort


class InMemoryEventQueue(EventQueuePort):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[Event, Channel]] = asyncio.Queue()

    async def enqueue(self, event: Event, channel: Channel) -> None:
        await self._queue.put((event, channel))

    async def dequeue(self) -> tuple[Event, Channel]:
        return await self._queue.get()
