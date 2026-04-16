from sqlalchemy import select

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import ProviderAccountModel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort


class PostgresProviderAccountRepository(ProviderAccountRepositoryPort):
    """Postgres adapter for provider account and default-account resolution."""

    async def create(self, provider_account: ProviderAccount) -> ProviderAccount:
        """Persist a provider account record."""

        async with AsyncSessionLocal() as session:
            model = ProviderAccountModel(
                provider_account_id=provider_account.provider_account_id,
                workspace_id=provider_account.workspace_id,
                provider_key=provider_account.provider_key,
                credentials=dict(provider_account.credentials),
                is_default=provider_account.is_default,
                is_active=provider_account.is_active,
                created_at=provider_account.created_at,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def get_by_id(self, provider_account_id: str) -> ProviderAccount | None:
        """Fetch a provider account by primary key."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ProviderAccountModel).where(ProviderAccountModel.provider_account_id == provider_account_id)
            )
            model = result.scalar_one_or_none()
            return self._to_domain(model)

    async def list_by_workspace(self, workspace_id: str) -> list[ProviderAccount]:
        """List provider accounts for a workspace ordered by newest first."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ProviderAccountModel)
                .where(ProviderAccountModel.workspace_id == workspace_id)
                .order_by(ProviderAccountModel.created_at.desc())
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def get_default(self, provider_key: str, workspace_id: str | None = None) -> ProviderAccount | None:
        """Fetch active default account for a provider in workspace/system scope."""

        async with AsyncSessionLocal() as session:
            stmt = (
                select(ProviderAccountModel)
                .where(ProviderAccountModel.provider_key == provider_key)
                .where(ProviderAccountModel.is_default.is_(True))
                .where(ProviderAccountModel.is_active.is_(True))
            )
            if workspace_id is None:
                stmt = stmt.where(ProviderAccountModel.workspace_id.is_(None))
            else:
                stmt = stmt.where(ProviderAccountModel.workspace_id == workspace_id)

            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model)

    @staticmethod
    def _to_domain(model: ProviderAccountModel | None) -> ProviderAccount | None:
        if model is None:
            return None
        return ProviderAccount(
            provider_account_id=model.provider_account_id,
            workspace_id=model.workspace_id,
            provider_key=model.provider_key,
            credentials=dict(model.credentials or {}),
            is_default=model.is_default,
            is_active=model.is_active,
            created_at=model.created_at,
        )
