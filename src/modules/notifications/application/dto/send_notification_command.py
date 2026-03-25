from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class SendNotificationCommand:
    """
    Purpose:
    - Carry input data for notification submission use case.

    Responsibilities:
    - Provide an immutable application-level command contract.

    Inputs:
    - workspace_id: str
    - event_id: str
    - event_name: str
    - payload: dict[str, Any]

    Outputs:
    - SendNotificationCommand DTO.

    Constraints:
    - Payload must be dict-based for schema flexibility.
    """

    workspace_id: str
    event_id: str
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
