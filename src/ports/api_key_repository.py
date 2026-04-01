from abc import ABC, abstractmethod

from src.domain.auth.entities import ApiKey


class ApiKeyRepository(ABC):
    @abstractmethod
    async def create(self, workspace_id: str, key_hash: str, name: str) -> ApiKey:
        ...

    @abstractmethod
    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[ApiKey]:
        ...

    @abstractmethod
    async def get_by_id(self, api_key_id: str) -> ApiKey | None:
        ...

    @abstractmethod
    async def disable(self, api_key_id: str) -> ApiKey | None:
        ...
