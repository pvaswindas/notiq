from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, frozen=True)
class Event:
    """
    Purpose:
    - Represent a generic notification event payload.

    Responsibilities:
    - Store immutable event context for routing and delivery.

    Inputs:
    - event_id: str
    - workspace_id: str
    - event_name: str
    - payload: dict[str, Any]
    - occurred_at: datetime

    Outputs:
    - Event entity instance.

    Constraints:
    - Payload schema must remain generic and dict-based.

    Attributes:
    - event_id: Stable event identifier.
    - workspace_id: Tenant identifier owning the event.
    - event_name: Logical event type name.
    - payload: Arbitrary event content.
    - occurred_at: UTC timestamp when the event occurred.
    """

    event_id: str
    workspace_id: str
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
