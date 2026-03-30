import json

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.event import Event


class EventMessageMapper:
    """Map domain event/channel context into a provider-ready message string."""

    def to_message(self, event: Event, channel: Channel) -> str:
        """Build a deterministic text payload for downstream provider adapters."""

        payload_text = json.dumps(event.payload, sort_keys=True)
        return (
            f"[{event.event_name}] workspace={event.workspace_id} "
            f"channel={channel.channel_id} destination={channel.destination} payload={payload_text}"
        )
