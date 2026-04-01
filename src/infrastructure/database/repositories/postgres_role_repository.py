from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.domain.admin.entities import Permission, Role
from src.infrastructure.database.models import AdminRoleModel, PermissionModel, RoleModel, RolePermissionModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.role_repository import RoleRepository


class PostgresRoleRepository(RoleRepository):
    async def create(self, name: str) -> Role:
        async with AsyncSessionLocal() as session:
            model = RoleModel(
                id=f"role_{uuid4().hex[:24]}",
                name=name,
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_role(model)

    async def get_by_id(self, role_id: str) -> Role | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(RoleModel, role_id)
            if model is None:
                return None
            return self._to_role(model)

    async def get_by_name(self, name: str) -> Role | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RoleModel).where(RoleModel.name == name))
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_role(model)

    async def list_all(self) -> list[Role]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RoleModel).order_by(RoleModel.created_at.asc()))
            return [self._to_role(model) for model in result.scalars().all()]

    async def assign_permission(self, role_id: str, permission_id: str) -> None:
        async with AsyncSessionLocal() as session:
            statement = insert(RolePermissionModel).values(role_id=role_id, permission_id=permission_id)
            statement = statement.on_conflict_do_nothing(index_elements=["role_id", "permission_id"])
            await session.execute(statement)
            await session.commit()

    async def list_permissions(self, role_id: str) -> list[Permission]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PermissionModel)
                .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
                .where(RolePermissionModel.role_id == role_id)
                .order_by(PermissionModel.name.asc())
            )
            return [self._to_permission(model) for model in result.scalars().all()]

    async def list_by_admin(self, admin_id: str) -> list[Role]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RoleModel)
                .join(AdminRoleModel, AdminRoleModel.role_id == RoleModel.id)
                .where(AdminRoleModel.admin_id == admin_id)
                .order_by(RoleModel.name.asc())
            )
            return [self._to_role(model) for model in result.scalars().all()]

    @staticmethod
    def _to_role(model: RoleModel) -> Role:
        return Role(id=model.id, name=model.name, created_at=model.created_at)

    @staticmethod
    def _to_permission(model: PermissionModel) -> Permission:
        return Permission(id=model.id, name=model.name, created_at=model.created_at)
