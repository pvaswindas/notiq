from dataclasses import asdict

from src.adapters.tasks.send_notification_task import send_notification_task
from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.ports.event_queue_port import EventQueuePort


class CeleryEventQueue(EventQueuePort):
    """Queue adapter that publishes legacy event-channel work to Celery.

    Architectural role:
    - Infrastructure adapter for compatibility ingestion flow.
    - Delegates actual task execution scheduling to Celery transport.
    """

    async def enqueue(self, event: Event, channel: Channel) -> None:
        """Serialize event/channel and publish async task message.

        Args:
            event: Legacy domain event to deliver.
            channel: Legacy channel target for delivery.

        Returns:
            None.

        Internal flow:
        - Convert dataclass entities to serializable dict payloads.
        - Dispatch `notiq.send_notification` Celery task.
        """

        event_payload = asdict(event)
        channel_payload = asdict(channel)
        send_notification_task.delay(event_payload=event_payload, channel_payload=channel_payload)

    async def dequeue(self) -> tuple[Event, Channel]:
        """Signal that dequeue semantics are owned by Celery workers.

        Raises:
            NotImplementedError: Always, because this adapter is publish-only.
        """

        raise NotImplementedError("dequeue is handled by Celery workers")
