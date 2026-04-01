from abc import ABC, abstractmethod

from src.domain.admin.entities import Permission


class PermissionRepository(ABC):
    @abstractmethod
    async def create(self, name: str) -> Permission:
        ...

    @abstractmethod
    async def get_by_id(self, permission_id: str) -> Permission | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Permission | None:
        ...

    @abstractmethod
    async def list_all(self) -> list[Permission]:
        ...

    @abstractmethod
    async def list_by_admin(self, admin_id: str) -> list[Permission]:
        ...

    @abstractmethod
    async def admin_has_permission(self, admin_id: str, permission_name: str) -> bool:
        ...
