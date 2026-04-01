from sqlalchemy import select
from uuid import uuid4

from src.domain.auth.entities import ApiKey
from src.infrastructure.database.models import ApiKeyModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.api_key_repository import ApiKeyRepository


class PostgresApiKeyRepository(ApiKeyRepository):
    async def create(self, workspace_id: str, key_hash: str, name: str) -> ApiKey:
        async with AsyncSessionLocal() as session:
            model = ApiKeyModel(
                id=f"key_{uuid4().hex[:24]}",
                workspace_id=workspace_id,
                key_hash=key_hash,
                name=name,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash))
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def list_by_workspace(self, workspace_id: str) -> list[ApiKey]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ApiKeyModel)
                .where(ApiKeyModel.workspace_id == workspace_id)
                .order_by(ApiKeyModel.created_at.desc())
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def get_by_id(self, api_key_id: str) -> ApiKey | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(ApiKeyModel, api_key_id)
            if model is None:
                return None
            return self._to_domain(model)

    async def disable(self, api_key_id: str) -> ApiKey | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(ApiKeyModel, api_key_id)
            if model is None:
                return None
            model.is_active = False
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    @staticmethod
    def _to_domain(model: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=model.id,
            workspace_id=model.workspace_id,
            key_hash=model.key_hash,
            name=model.name,
            is_active=model.is_active,
            created_at=model.created_at,
        )
