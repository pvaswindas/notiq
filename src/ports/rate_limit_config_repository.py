from abc import ABC, abstractmethod

from src.domain.rate_limit.entities import RateLimitConfig


class RateLimitConfigRepositoryPort(ABC):
    """Port for retrieving scoped rate-limit policies.

    Architectural role:
    - Defines read-only configuration access for the legacy rate-limit
      resolver without binding application code to storage details.
    """

    @abstractmethod
    def get_group_config(self, group: str) -> RateLimitConfig | None:
        """Fetch group-scoped policy for a channel group if present.

        Args:
            group: Channel grouping identifier.

        Returns:
            RateLimitConfig | None: Group policy when configured, otherwise None.
        """

        ...

    @abstractmethod
    def get_provider_config(self, provider: str) -> RateLimitConfig | None:
        """Fetch provider-scoped policy for a delivery provider.

        Args:
            provider: Provider key (for example `telegram`).

        Returns:
            RateLimitConfig | None: Provider policy when configured, otherwise None.
        """

        ...

    @abstractmethod
    def get_tenant_config(self, workspace_id: str) -> RateLimitConfig | None:
        """Fetch tenant-scoped policy for a workspace.

        Args:
            workspace_id: Workspace identifier for legacy event flow.

        Returns:
            RateLimitConfig | None: Tenant policy when configured, otherwise None.
        """

        ...

    @abstractmethod
    def get_global_config(self) -> RateLimitConfig:
        """Fetch required global fallback policy.

        Returns:
            RateLimitConfig: Default policy used when no narrower scope exists.
        """

        ...
