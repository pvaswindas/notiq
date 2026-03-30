from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class Event:
    workspace_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("workspace_id is required")
        if not self.event_type:
            raise ValueError("event_type is required")
