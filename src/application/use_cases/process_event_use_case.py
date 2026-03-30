from src.domain.entities.event import Event
from src.ports.channel_repository_port import ChannelRepositoryPort
from src.ports.event_queue_port import EventQueuePort


class ProcessEventUseCase:
    def __init__(
        self,
        channel_repository: ChannelRepositoryPort,
        event_queue: EventQueuePort,
    ) -> None:
        self._channel_repository = channel_repository
        self._event_queue = event_queue

    async def execute(self, event: Event) -> None:
        channels = await self._channel_repository.get_active_channels(event.workspace_id)
        for channel in channels:
            await self._event_queue.enqueue(event, channel)
