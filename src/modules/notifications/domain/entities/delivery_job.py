from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class DeliveryJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(slots=True, frozen=True)
class DeliveryJob:
    """
    Purpose:
    - Represent an asynchronous delivery unit derived from an event and channel.

    Responsibilities:
    - Carry immutable dispatch data through persistence-backed processing.

    Inputs:
    - job_id: str
    - workspace_id: str
    - channel_id: str
    - provider_key: str
    - destination: str
    - message: str
    - dedupe_key: str
    - status: DeliveryJobStatus
    - retry_count: int
    - max_retries: int
    - last_error: str | None
    - next_retry_at: datetime | None
    - created_at: datetime

    Outputs:
    - DeliveryJob aggregate instance.

    Constraints:
    - retry_count must be non-negative.
    - max_retries must be at least 1.
    """

    job_id: str
    workspace_id: str
    channel_id: str
    provider_key: str
    destination: str
    message: str
    dedupe_key: str
    status: DeliveryJobStatus = DeliveryJobStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    last_error: str | None = None
    next_retry_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least 1")
