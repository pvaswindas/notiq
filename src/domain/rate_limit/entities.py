from dataclasses import dataclass
from typing import Literal


RateLimitScope = Literal["group", "provider", "tenant", "global"]


@dataclass(slots=True, frozen=True)
class RateLimitConfig:
    scope: RateLimitScope
    key: str
    limit: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("limit must be greater than 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be greater than 0")
        if not self.key:
            raise ValueError("key is required")
