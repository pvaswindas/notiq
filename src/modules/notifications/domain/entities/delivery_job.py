from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True, frozen=True)
class DeliveryJob:
    """
    Purpose:
    - Represent an asynchronous delivery unit derived from an event and channel.

    Responsibilities:
    - Carry immutable dispatch data through queue-based processing.

    Inputs:
    - job_id: str
    - workspace_id: str
    - channel_id: str
    - provider_key: str
    - destination: str
    - message: str
    - dedupe_key: str
    - attempt: int
    - max_attempts: int
    - created_at: datetime

    Outputs:
    - DeliveryJob aggregate instance.

    Constraints:
    - Attempt value must be non-negative.

    Attributes:
    - job_id: Stable queue item identifier.
    - workspace_id: Tenant identifier.
    - channel_id: Channel identifier used for delivery.
    - provider_key: Provider routing key.
    - destination: Provider destination address.
    - message: Normalized outbound message.
    - dedupe_key: Idempotency fingerprint.
    - attempt: Current retry attempt counter.
    - max_attempts: Maximum retry allowance.
    - created_at: UTC timestamp when job was created.
    """

    job_id: str
    workspace_id: str
    channel_id: str
    provider_key: str
    destination: str
    message: str
    dedupe_key: str
    attempt: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
