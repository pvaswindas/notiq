from src.domain.entities.event import Event
from src.ports.channel_repository_port import ChannelRepositoryPort
from src.ports.event_queue_port import EventQueuePort


class ProcessEventUseCase:
    """Fan out a legacy event to active channels via queue adapter.

    Architectural role:
    - Compatibility application use case for `/events` ingestion path.
    - Coordinates channel lookup and queue enqueueing, but intentionally
      avoids provider-delivery or persistence-specific logic.
    """

    def __init__(
        self,
        channel_repository: ChannelRepositoryPort,
        event_queue: EventQueuePort,
    ) -> None:
        """Initialize dependencies needed for legacy event fan-out.

        Args:
            channel_repository: Port used to load active channels per workspace.
            event_queue: Port used to enqueue `(event, channel)` work items.
        """

        self._channel_repository = channel_repository
        self._event_queue = event_queue

    async def execute(self, event: Event) -> None:
        """Enqueue one queue message per active channel for the workspace.

        Args:
            event: Validated legacy domain event to fan out.

        Returns:
            None.

        Internal flow:
        - Load all active channels for `event.workspace_id`.
        - Enqueue an independent queue item for each selected channel.

        Edge cases and constraints:
        - If no channels are active, the method exits without enqueueing.
        - Queue-level failure for any enqueue bubbles to caller.
        """

        channels = await self._channel_repository.get_active_channels(event.workspace_id)
        for channel in channels:
            await self._event_queue.enqueue(event, channel)
