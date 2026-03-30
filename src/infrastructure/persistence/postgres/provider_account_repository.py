from sqlalchemy import select

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import ProviderAccountModel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort


class PostgresProviderAccountRepository(ProviderAccountRepositoryPort):
    """Postgres adapter for provider account and default-account resolution."""

    async def get_by_id(self, provider_account_id: str) -> ProviderAccount | None:
        """Fetch a provider account by primary key."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ProviderAccountModel).where(ProviderAccountModel.provider_account_id == provider_account_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return ProviderAccount(
                provider_account_id=model.provider_account_id,
                workspace_id=model.workspace_id,
                provider_key=model.provider_key,
                credentials_ref=model.credentials_ref,
                is_default=model.is_default,
                is_active=model.is_active,
                created_at=model.created_at,
            )

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
            if model is None:
                return None
            return ProviderAccount(
                provider_account_id=model.provider_account_id,
                workspace_id=model.workspace_id,
                provider_key=model.provider_key,
                credentials_ref=model.credentials_ref,
                is_default=model.is_default,
                is_active=model.is_active,
                created_at=model.created_at,
            )
