from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import exists, select

from src.domain.admin.entities import Permission
from src.infrastructure.database.models import AdminRoleModel, PermissionModel, RolePermissionModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.permission_repository import PermissionRepository


class PostgresPermissionRepository(PermissionRepository):
    async def create(self, name: str) -> Permission:
        async with AsyncSessionLocal() as session:
            model = PermissionModel(
                id=f"perm_{uuid4().hex[:24]}",
                name=name,
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def get_by_id(self, permission_id: str) -> Permission | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(PermissionModel, permission_id)
            if model is None:
                return None
            return self._to_domain(model)

    async def get_by_name(self, name: str) -> Permission | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PermissionModel).where(PermissionModel.name == name))
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def list_all(self) -> list[Permission]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PermissionModel).order_by(PermissionModel.created_at.asc()))
            return [self._to_domain(model) for model in result.scalars().all()]

    async def list_by_admin(self, admin_id: str) -> list[Permission]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PermissionModel)
                .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
                .join(AdminRoleModel, AdminRoleModel.role_id == RolePermissionModel.role_id)
                .where(AdminRoleModel.admin_id == admin_id)
                .distinct()
                .order_by(PermissionModel.name.asc())
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def admin_has_permission(self, admin_id: str, permission_name: str) -> bool:
        async with AsyncSessionLocal() as session:
            statement = select(
                exists()
                .where(AdminRoleModel.admin_id == admin_id)
                .where(AdminRoleModel.role_id == RolePermissionModel.role_id)
                .where(RolePermissionModel.permission_id == PermissionModel.id)
                .where(PermissionModel.name == permission_name)
            )
            result = await session.execute(statement)
            return bool(result.scalar())

    @staticmethod
    def _to_domain(model: PermissionModel) -> Permission:
        return Permission(id=model.id, name=model.name, created_at=model.created_at)
