import asyncio

from sqlalchemy import or_, select

from src.domain.rate_limit.entities import RateLimitConfig
from src.infrastructure.database.models import RateLimitConfigModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.rate_limit_config_repository import RateLimitConfigRepository


class PostgresRateLimitConfigRepository(RateLimitConfigRepository):
    async def get_by_id(self, config_id: str, workspace_id: str) -> RateLimitConfig | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RateLimitConfigModel)
                .where(RateLimitConfigModel.id == config_id)
                .where(or_(RateLimitConfigModel.workspace_id == workspace_id, RateLimitConfigModel.workspace_id.is_(None)))
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def list_by_workspace(self, workspace_id: str) -> list[RateLimitConfig]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RateLimitConfigModel).where(
                    or_(RateLimitConfigModel.workspace_id == workspace_id, RateLimitConfigModel.workspace_id.is_(None))
                )
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, config: RateLimitConfig) -> RateLimitConfig:
        if config.id is None:
            raise ValueError("RateLimitConfig.id is required for persistence")

        async with AsyncSessionLocal() as session:
            model = self._to_model(config)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def update(self, config: RateLimitConfig) -> RateLimitConfig:
        if config.id is None:
            raise ValueError("RateLimitConfig.id is required for persistence")

        async with AsyncSessionLocal() as session:
            model = await session.get(RateLimitConfigModel, config.id)
            if model is None:
                model = self._to_model(config)
                session.add(model)
            else:
                model.workspace_id = config.workspace_id
                model.scope = config.scope
                model.key = config.key
                model.limit = config.limit
                model.window_seconds = config.window_seconds
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    def get_group_config(self, group: str, workspace_id: str | None = None) -> RateLimitConfig | None:
        return self._run_sync(self._get_scope_config(scope="group", key=group, workspace_id=workspace_id))

    def get_provider_config(self, provider: str, workspace_id: str | None = None) -> RateLimitConfig | None:
        return self._run_sync(self._get_scope_config(scope="provider", key=provider.strip().lower(), workspace_id=workspace_id))

    def get_tenant_config(self, workspace_id: str) -> RateLimitConfig | None:
        return self._run_sync(self._get_scope_config(scope="tenant", key=workspace_id, workspace_id=workspace_id))

    def get_global_config(self) -> RateLimitConfig:
        config = self._run_sync(self._get_scope_config(scope="global", key="default", workspace_id=None))
        if config is None:
            raise ValueError("Global rate-limit config is not configured")
        return config

    async def _get_scope_config(self, scope: str, key: str, workspace_id: str | None) -> RateLimitConfig | None:
        async with AsyncSessionLocal() as session:
            where_clause = [RateLimitConfigModel.scope == scope, RateLimitConfigModel.key == key]
            if workspace_id is None:
                where_clause.append(RateLimitConfigModel.workspace_id.is_(None))
            else:
                where_clause.append(
                    or_(RateLimitConfigModel.workspace_id == workspace_id, RateLimitConfigModel.workspace_id.is_(None))
                )

            result = await session.execute(select(RateLimitConfigModel).where(*where_clause))
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    @staticmethod
    def _run_sync(coro: "asyncio.Future[RateLimitConfig | None]") -> RateLimitConfig | None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError("Synchronous rate-limit lookup cannot run inside an active event loop")
        return asyncio.run(coro)

    @staticmethod
    def _to_domain(model: RateLimitConfigModel) -> RateLimitConfig:
        return RateLimitConfig(
            id=model.id,
            workspace_id=model.workspace_id,
            scope=model.scope,
            key=model.key,
            limit=model.limit,
            window_seconds=model.window_seconds,
        )

    @staticmethod
    def _to_model(config: RateLimitConfig) -> RateLimitConfigModel:
        if config.id is None:
            raise ValueError("RateLimitConfig.id is required for persistence")

        return RateLimitConfigModel(
            id=config.id,
            workspace_id=config.workspace_id,
            scope=config.scope,
            key=config.key,
            limit=config.limit,
            window_seconds=config.window_seconds,
        )
