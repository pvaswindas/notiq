import json

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.event import Event


class EventMessageMapper:
    def to_message(self, event: Event, channel: Channel) -> str:
        payload_text = json.dumps(event.payload, sort_keys=True)
        return (
            f"[{event.event_name}] workspace={event.workspace_id} "
            f"channel={channel.channel_id} destination={channel.destination} payload={payload_text}"
        )
