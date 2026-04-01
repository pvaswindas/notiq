from dataclasses import dataclass

from fastapi import HTTPException, status

from src.application.services.audit_logger import AuditLogger
from src.ports.admin_repository import AdminRepository
from src.ports.role_repository import RoleRepository


@dataclass(slots=True, frozen=True)
class AssignRoleInput:
    """Input contract for assigning one role to one admin."""

    admin_id: str
    role_id: str
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class AssignRoleUseCase:
    """Assign roles to admins after validating both entities exist.

    Architectural role:
    - Application coordinator for RBAC membership mutation.
    """

    def __init__(
        self,
        admin_repository: AdminRepository,
        role_repository: RoleRepository,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """Store repositories required for admin-role assignment flow."""

        self._admin_repository = admin_repository
        self._role_repository = role_repository
        self._audit_logger = audit_logger

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

        before_roles = await self._role_repository.list_by_admin(dto.admin_id)

        await self._admin_repository.assign_role(admin_id=dto.admin_id, role_id=dto.role_id)

        if self._audit_logger is not None:
            after_roles = await self._role_repository.list_by_admin(dto.admin_id)
            await self._audit_logger.log(
                actor_id=dto.actor_id,
                action="admin.assign_role",
                resource="admin",
                resource_id=dto.admin_id,
                before={"roles": [assigned_role.name for assigned_role in before_roles]},
                after={"roles": [assigned_role.name for assigned_role in after_roles]},
                metadata={
                    "role_id": dto.role_id,
                    **(dto.audit_metadata or {}),
                },
            )
