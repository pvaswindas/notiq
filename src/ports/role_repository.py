from abc import ABC, abstractmethod

from src.domain.admin.entities import Permission, Role


class RoleRepository(ABC):
    @abstractmethod
    async def create(self, name: str) -> Role:
        ...

    @abstractmethod
    async def get_by_id(self, role_id: str) -> Role | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None:
        ...

    @abstractmethod
    async def list_all(self) -> list[Role]:
        ...

    @abstractmethod
    async def assign_permission(self, role_id: str, permission_id: str) -> None:
        ...

    @abstractmethod
    async def list_permissions(self, role_id: str) -> list[Permission]:
        ...

    @abstractmethod
    async def list_by_admin(self, admin_id: str) -> list[Role]:
        ...
