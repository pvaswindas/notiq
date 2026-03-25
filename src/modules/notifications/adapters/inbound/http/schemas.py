from typing import Any

from pydantic import BaseModel, Field


class SendNotificationRequest(BaseModel):
    """
    Purpose:
    - Define HTTP request payload for notification submission.

    Responsibilities:
    - Validate inbound API data before application mapping.

    Inputs:
    - workspace_id: str
    - event_id: str
    - event_name: str
    - payload: dict[str, Any]

    Outputs:
    - Validated request model.

    Constraints:
    - Payload must remain dict-based and generic.
    """

    workspace_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_name: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class SendNotificationResponse(BaseModel):
    """
    Purpose:
    - Define HTTP response payload for notification submission.

    Responsibilities:
    - Expose enqueue result in API-friendly structure.

    Inputs:
    - enqueued_jobs: int
    - skipped_duplicates: int

    Outputs:
    - Response model for clients.

    Constraints:
    - Counts must be non-negative integers.
    """

    enqueued_jobs: int
    skipped_duplicates: int
