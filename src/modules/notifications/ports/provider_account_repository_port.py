from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.provider_account import ProviderAccount


class ProviderAccountRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, provider_account_id: str) -> ProviderAccount | None:
        pass

    @abstractmethod
    async def get_default(self, provider_key: str, workspace_id: str | None = None) -> ProviderAccount | None:
        pass
