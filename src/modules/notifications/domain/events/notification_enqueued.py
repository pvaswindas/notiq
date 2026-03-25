from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NotificationEnqueued:
    """
    Purpose:
    - Represent successful queueing of a delivery job.

    Responsibilities:
    - Capture immutable metadata for workflow observability.

    Inputs:
    - workspace_id: str
    - job_id: str
    - channel_id: str

    Outputs:
    - NotificationEnqueued domain event.

    Constraints:
    - Event data must remain immutable.
    """

    workspace_id: str
    job_id: str
    channel_id: str
