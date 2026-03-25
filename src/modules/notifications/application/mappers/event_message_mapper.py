import json

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.event import Event


class EventMessageMapper:
    """
    Purpose:
    - Transform domain events into outbound message text.

    Responsibilities:
    - Convert generic event payload into deterministic text payload.
    - Implement message mapper port used by application use cases.

    Inputs:
    - event: Event
    - channel: Channel

    Outputs:
    - str message body.

    Constraints:
    - Must remain deterministic and provider-agnostic.
    """

    def to_message(self, event: Event, channel: Channel) -> str:
        """
        Purpose:
        - Build outbound message content from event data.

        Responsibilities:
        - Serialize event payload in stable JSON format.

        Inputs:
        - event: Event
        - channel: Channel

        Outputs:
        - str

        Constraints:
        - Payload must be JSON-serializable.
        """

        payload_text = json.dumps(event.payload, sort_keys=True)
        return f"[{event.event_name}] workspace={event.workspace_id} channel={channel.name} payload={payload_text}"
