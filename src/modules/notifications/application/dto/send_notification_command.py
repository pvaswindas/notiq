from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class SendNotificationCommand:
    workspace_id: str
    event_id: str
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    channel_ids: list[str] | None = None
