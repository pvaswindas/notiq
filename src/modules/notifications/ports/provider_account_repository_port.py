from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.provider_account import ProviderAccount


class ProviderAccountRepositoryPort(ABC):
    """Port for loading provider-account credentials and defaults."""

    @abstractmethod
    async def get_by_id(self, provider_account_id: str) -> ProviderAccount | None:
        """Fetch provider account by identifier."""

        pass

    @abstractmethod
    async def get_default(self, provider_key: str, workspace_id: str | None = None) -> ProviderAccount | None:
        """Fetch default provider account for workspace or system scope."""

        pass
