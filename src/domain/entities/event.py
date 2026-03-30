from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class Event:
    """Legacy ingestion event entity used by `/events` compatibility path.

    Purpose:
    - Represent minimal event data required for channel fan-out tasks.

    Responsibilities:
    - Enforce presence of workspace and event type identifiers.
    - Carry flexible payload for provider-specific formatting downstream.

    Architectural role:
    - Legacy domain model retained for backward compatibility.

    Constraints:
    - `workspace_id` and `event_type` must be non-empty strings.
    """

    workspace_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate required identifiers used by queue fan-out logic.

        Raises:
            ValueError: If workspace_id or event_type is empty.
        """

        if not self.workspace_id:
            raise ValueError("workspace_id is required")
        if not self.event_type:
            raise ValueError("event_type is required")
