from sqlalchemy import select

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import ChannelModel
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.ports.channel_repository_port import ChannelRepositoryPort


class PostgresChannelRepository(ChannelRepositoryPort):
    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.workspace_id == workspace_id)
                .where(ChannelModel.is_active.is_(True))
            )
            models = result.scalars().all()
            return [
                Channel(
                    channel_id=model.channel_id,
                    workspace_id=model.workspace_id,
                    provider_key=model.provider_key,
                    destination=model.destination,
                    provider_account_id=model.provider_account_id,
                    is_active=model.is_active,
                    metadata=model.metadata_json,
                    created_at=model.created_at,
                )
                for model in models
            ]
