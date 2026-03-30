from abc import ABC, abstractmethod

from src.domain.rate_limit.entities import RateLimitConfig


class RateLimitConfigRepositoryPort(ABC):
    @abstractmethod
    def get_group_config(self, group: str) -> RateLimitConfig | None:
        ...

    @abstractmethod
    def get_provider_config(self, provider: str) -> RateLimitConfig | None:
        ...

    @abstractmethod
    def get_tenant_config(self, workspace_id: str) -> RateLimitConfig | None:
        ...

    @abstractmethod
    def get_global_config(self) -> RateLimitConfig:
        ...
