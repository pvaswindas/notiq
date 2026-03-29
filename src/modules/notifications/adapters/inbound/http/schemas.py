from typing import Any

from pydantic import BaseModel, Field


class SendNotificationRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_name: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    channel_ids: list[str] | None = None


class SendNotificationResponse(BaseModel):
    enqueued_jobs: int
    skipped_duplicates: int
