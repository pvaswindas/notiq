from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, frozen=True)
class DeadLetterJob:
    """Durable record of a delivery job that exhausted retries and failed permanently."""

    dead_letter_job_id: str
    original_job_id: str
    workspace_id: str
    channel_id: str
    provider: str
    payload: dict[str, Any]
    failure_reason: str
    failure_count: int
    last_attempt_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

