from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NotificationRequested:
    """
    Purpose:
    - Represent the intent to dispatch a notification event.

    Responsibilities:
    - Capture immutable metadata for audit and tracing.

    Inputs:
    - workspace_id: str
    - event_id: str

    Outputs:
    - NotificationRequested domain event.

    Constraints:
    - Event data must remain immutable.
    """

    workspace_id: str
    event_id: str
