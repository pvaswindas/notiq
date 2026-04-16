from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class DeliveryJobStatus(StrEnum):
    """Lifecycle states for a persisted delivery job."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(slots=True, frozen=True)
class DeliveryJob:
    """Executable delivery unit created from an event-channel pairing.

    The worker advances this entity through `PENDING -> PROCESSING -> SUCCESS`
    or `FAILED` while maintaining retry and error metadata.
    """

    job_id: str
    workspace_id: str
    channel_id: str
    provider_key: str
    destination: str
    message: str
    event_payload: dict[str, Any]
    dedupe_key: str
    provider_account_id: str | None = None
    status: DeliveryJobStatus = DeliveryJobStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    processing_owner: str | None = None
    processing_expires_at: datetime | None = None
    last_error: str | None = None
    next_retry_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate retry invariants required for reliable job processing."""

        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least 1")
