from abc import ABC, abstractmethod

from src.domain.rate_limit.entities import RateLimitConfig


class RateLimiterPort(ABC):
    """Port for enforcing rate limits against a concrete counter backend.

    Architectural role:
    - Keeps application/task flow independent from Redis or any other
      implementation chosen for request counting.
    """

    @abstractmethod
    def allow(self, config: RateLimitConfig) -> bool:
        """Check whether one execution is allowed under the given policy.

        Args:
            config: Scoped throttle configuration to enforce.

        Returns:
            bool: True when execution can proceed; False when throttled.
        """

        ...
