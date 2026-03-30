from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limit_config_repository import RateLimitConfigRepositoryPort


class RateLimitResolver:
    """Resolve the effective throttle policy for legacy event delivery tasks.

    Purpose:
    - Centralize rate-limit selection for the compatibility Celery pipeline.

    Responsibilities:
    - Apply the configured fallback order across group, provider, tenant,
      and global scopes.

    Architectural role:
    - Legacy application service that translates domain context into a
      `RateLimitConfig` without performing infrastructure calls directly.
    """

    def __init__(self, config_repository: RateLimitConfigRepositoryPort) -> None:
        """Store repository port used for rate-limit policy lookup.

        Args:
            config_repository: Port implementation that provides scoped
                rate-limit configuration entries.
        """

        self._config_repository = config_repository

    def resolve(self, event: Event, channel: Channel) -> RateLimitConfig:
        """Select the first matching rate-limit configuration for a delivery.

        Args:
            event: Legacy event that carries tenant/workspace context.
            channel: Legacy channel that carries provider and optional group.

        Returns:
            RateLimitConfig: The resolved configuration to enforce.

        Internal flow:
        - Try group-level policy when channel group is present.
        - Fallback to provider-level policy.
        - Fallback to tenant-level policy.
        - Always return global default as final fallback.

        Edge cases and constraints:
        - Missing scope entries are expected and trigger fallback.
        - Global policy must always be present in repository implementation.
        """

        group = channel.group
        if group:
            group_config = self._config_repository.get_group_config(group)
            if group_config is not None:
                return group_config

        provider_config = self._config_repository.get_provider_config(channel.provider)
        if provider_config is not None:
            return provider_config

        tenant_config = self._config_repository.get_tenant_config(event.workspace_id)
        if tenant_config is not None:
            return tenant_config

        return self._config_repository.get_global_config()
