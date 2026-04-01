from dataclasses import dataclass

from fastapi import HTTPException, status

from src.ports.admin_repository import AdminRepository
from src.ports.role_repository import RoleRepository


@dataclass(slots=True, frozen=True)
class AssignRoleInput:
    """Input contract for assigning one role to one admin."""

    admin_id: str
    role_id: str


class AssignRoleUseCase:
    """Assign roles to admins after validating both entities exist.

    Architectural role:
    - Application coordinator for RBAC membership mutation.
    """

    def __init__(
        self,
        admin_repository: AdminRepository,
        role_repository: RoleRepository,
    ) -> None:
        """Store repositories required for admin-role assignment flow."""

        self._admin_repository = admin_repository
        self._role_repository = role_repository

    async def execute(self, dto: AssignRoleInput) -> None:
        """Assign role membership to an admin.

        Args:
            dto: Assignment input containing target admin and role ids.

        Returns:
            None: Side-effecting operation that persists admin-role linkage.

        Internal flow:
        - Validate admin existence.
        - Validate role existence.
        - Persist relationship in repository.

        Edge cases and constraints:
        - Missing admin/role results in `404`.
        - Function must not perform direct transport-layer mapping.
        """

        admin = await self._admin_repository.get_by_id(dto.admin_id)
        if admin is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin not found")

        role = await self._role_repository.get_by_id(dto.role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role not found")

        await self._admin_repository.assign_role(admin_id=dto.admin_id, role_id=dto.role_id)
