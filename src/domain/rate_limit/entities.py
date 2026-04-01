from dataclasses import dataclass
from typing import Literal


RateLimitScope = Literal["group", "provider", "tenant", "global"]


@dataclass(slots=True, frozen=True)
class RateLimitConfig:
    """Immutable throttle policy for compatibility delivery execution.

    Purpose:
    - Define a scoped limit and time window used by rate limiter adapters.

    Responsibilities:
    - Carry normalized policy data for resolver and limiter collaboration.

    Architectural role:
    - Legacy domain model shared by application services and rate-limit ports.

    Constraints:
    - `key` must be non-empty.
    - `limit` and `window_seconds` must be positive integers.
    """

    scope: RateLimitScope
    key: str
    limit: int
    window_seconds: int
    id: str | None = None
    workspace_id: str | None = None

    def __post_init__(self) -> None:
        """Validate policy invariants to keep limiter behavior well-defined.

        Raises:
            ValueError: If key is empty or numeric constraints are invalid.
        """

        if self.limit <= 0:
            raise ValueError("limit must be greater than 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be greater than 0")
        if not self.key:
            raise ValueError("key is required")
