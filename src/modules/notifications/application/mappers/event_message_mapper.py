import json

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.event import Event


class EventMessageMapper:
    """Map domain event/channel context into a provider-ready message string."""

    def to_message(self, event: Event, channel: Channel) -> str:
        """Build a deterministic text payload for downstream provider adapters."""

        message_value = event.payload.get("message")
        if not isinstance(message_value, str) or not message_value.strip():
            payload_text = json.dumps(event.payload, sort_keys=True)
            raise ValueError(
                f"event payload missing required string field 'message' for channel {channel.channel_id}: {payload_text}"
            )

        title_value = event.payload.get("title")
        title = title_value.strip() if isinstance(title_value, str) else ""
        message = message_value.strip()
        if title:
            return f"{title}\n{message}"
        return message
