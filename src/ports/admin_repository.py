from abc import ABC, abstractmethod

from src.domain.admin.entities import Admin


class AdminRepository(ABC):
    @abstractmethod
    async def create(self, name: str, email: str, password_hash: str) -> Admin:
        ...

    @abstractmethod
    async def get_by_id(self, admin_id: str) -> Admin | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Admin | None:
        ...

    @abstractmethod
    async def list_all(self) -> list[Admin]:
        ...

    @abstractmethod
    async def set_active(self, admin_id: str, is_active: bool) -> Admin | None:
        ...

    @abstractmethod
    async def assign_role(self, admin_id: str, role_id: str) -> None:
        ...
