from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limit_config_repository import RateLimitConfigRepositoryPort


class InMemoryRateLimitConfigRepository(RateLimitConfigRepositoryPort):
    """In-process rate-limit config source for legacy compatibility flow.

    Purpose:
    - Provide deterministic seeded throttle policy without external storage.

    Architectural role:
    - Infrastructure adapter implementing configuration lookup port.

    Constraints:
    - Intended for bootstrap defaults and local/runtime compatibility.
    - Policy values are static until process restart.
    """

    def __init__(self) -> None:
        """Seed known group/provider/tenant policies plus global fallback."""

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
        """Return group-scoped policy for exact group key match.

        Args:
            group: Channel group name from legacy channel entity.

        Returns:
            RateLimitConfig | None: Matched group policy or None.
        """

        return self._group_configs.get(group)

    def get_provider_config(self, provider: str) -> RateLimitConfig | None:
        """Return provider policy using normalized lowercase provider key.

        Args:
            provider: Provider identifier from channel route.

        Returns:
            RateLimitConfig | None: Matched provider policy or None.
        """

        return self._provider_configs.get(provider.strip().lower())

    def get_tenant_config(self, workspace_id: str) -> RateLimitConfig | None:
        """Return tenant policy for exact workspace identifier.

        Args:
            workspace_id: Workspace identifier from event payload.

        Returns:
            RateLimitConfig | None: Matched tenant policy or None.
        """

        return self._tenant_configs.get(workspace_id)

    def get_global_config(self) -> RateLimitConfig:
        """Return mandatory global fallback rate-limit policy."""

        return self._global_config
