from abc import ABC, abstractmethod

from src.domain.rate_limit.entities import RateLimitConfig


class RateLimiterPort(ABC):
    @abstractmethod
    def allow(self, config: RateLimitConfig) -> bool:
        ...
