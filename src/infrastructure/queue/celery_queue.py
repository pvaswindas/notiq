from dataclasses import asdict

from src.adapters.tasks.send_notification_task import send_notification_task
from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.ports.event_queue_port import EventQueuePort


class CeleryEventQueue(EventQueuePort):
    async def enqueue(self, event: Event, channel: Channel) -> None:
        event_payload = asdict(event)
        channel_payload = asdict(channel)
        send_notification_task.delay(event_payload=event_payload, channel_payload=channel_payload)

    async def dequeue(self) -> tuple[Event, Channel]:
        raise NotImplementedError("dequeue is handled by Celery workers")
