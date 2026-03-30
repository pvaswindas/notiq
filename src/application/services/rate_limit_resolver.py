from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limit_config_repository import RateLimitConfigRepositoryPort


class RateLimitResolver:
    def __init__(self, config_repository: RateLimitConfigRepositoryPort) -> None:
        self._config_repository = config_repository

    def resolve(self, event: Event, channel: Channel) -> RateLimitConfig:
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
