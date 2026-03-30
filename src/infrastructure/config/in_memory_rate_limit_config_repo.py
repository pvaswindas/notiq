from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limit_config_repository import RateLimitConfigRepositoryPort


class InMemoryRateLimitConfigRepository(RateLimitConfigRepositoryPort):
    def __init__(self) -> None:
        self._group_configs: dict[str, RateLimitConfig] = {
            "critical_alerts": RateLimitConfig(scope="group", key="critical_alerts", limit=5, window_seconds=1),
            "marketing": RateLimitConfig(scope="group", key="marketing", limit=2, window_seconds=1),
        }
        self._provider_configs: dict[str, RateLimitConfig] = {
            "telegram": RateLimitConfig(scope="provider", key="telegram", limit=30, window_seconds=1),
        }
        self._tenant_configs: dict[str, RateLimitConfig] = {
            "ws_123": RateLimitConfig(scope="tenant", key="ws_123", limit=50, window_seconds=1),
        }
        self._global_config = RateLimitConfig(scope="global", key="default", limit=1000, window_seconds=1)

    def get_group_config(self, group: str) -> RateLimitConfig | None:
        return self._group_configs.get(group)

    def get_provider_config(self, provider: str) -> RateLimitConfig | None:
        return self._provider_configs.get(provider.strip().lower())

    def get_tenant_config(self, workspace_id: str) -> RateLimitConfig | None:
        return self._tenant_configs.get(workspace_id)

    def get_global_config(self) -> RateLimitConfig:
        return self._global_config
