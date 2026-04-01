from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.domain.admin.entities import Admin
from src.infrastructure.database.models import AdminModel, AdminRoleModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.admin_repository import AdminRepository


class PostgresAdminRepository(AdminRepository):
    async def create(self, name: str, email: str, password_hash: str) -> Admin:
        async with AsyncSessionLocal() as session:
            model = AdminModel(
                id=f"adm_{uuid4().hex[:24]}",
                name=name,
                email=email,
                password_hash=password_hash,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def get_by_id(self, admin_id: str) -> Admin | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(AdminModel, admin_id)
            if model is None:
                return None
            return self._to_domain(model)

    async def get_by_email(self, email: str) -> Admin | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AdminModel).where(AdminModel.email == email))
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def list_all(self) -> list[Admin]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AdminModel).order_by(AdminModel.created_at.desc()))
            return [self._to_domain(model) for model in result.scalars().all()]

    async def set_active(self, admin_id: str, is_active: bool) -> Admin | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(AdminModel, admin_id)
            if model is None:
                return None
            model.is_active = is_active
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def assign_role(self, admin_id: str, role_id: str) -> None:
        async with AsyncSessionLocal() as session:
            statement = insert(AdminRoleModel).values(admin_id=admin_id, role_id=role_id)
            statement = statement.on_conflict_do_nothing(index_elements=["admin_id", "role_id"])
            await session.execute(statement)
            await session.commit()

    @staticmethod
    def _to_domain(model: AdminModel) -> Admin:
        return Admin(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            is_active=model.is_active,
            created_at=model.created_at,
        )
