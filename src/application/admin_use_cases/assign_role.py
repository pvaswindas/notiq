from dataclasses import dataclass

from fastapi import HTTPException, status

from src.ports.admin_repository import AdminRepository
from src.ports.role_repository import RoleRepository


@dataclass(slots=True, frozen=True)
class AssignRoleInput:
    admin_id: str
    role_id: str


class AssignRoleUseCase:
    def __init__(
        self,
        admin_repository: AdminRepository,
        role_repository: RoleRepository,
    ) -> None:
        self._admin_repository = admin_repository
        self._role_repository = role_repository

    async def execute(self, dto: AssignRoleInput) -> None:
        admin = await self._admin_repository.get_by_id(dto.admin_id)
        if admin is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin not found")

        role = await self._role_repository.get_by_id(dto.role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role not found")

        await self._admin_repository.assign_role(admin_id=dto.admin_id, role_id=dto.role_id)
