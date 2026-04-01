from src.ports.admin_repository import AdminRepository
from src.ports.permission_repository import PermissionRepository


class RbacService:
    def __init__(
        self,
        admin_repository: AdminRepository,
        permission_repository: PermissionRepository,
    ) -> None:
        self._admin_repository = admin_repository
        self._permission_repository = permission_repository

    async def has_permission(self, admin_id: str, permission_name: str) -> bool:
        admin = await self._admin_repository.get_by_id(admin_id)
        if admin is None or not admin.is_active:
            return False

        return await self._permission_repository.admin_has_permission(
            admin_id=admin_id,
            permission_name=permission_name,
        )
