from sqlalchemy import select

from src.domain.entities.channel import Channel
from src.infrastructure.database.models import ChannelModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.channel_repository import ChannelRepository
from src.ports.channel_repository_port import ChannelRepositoryPort


class PostgresChannelRepository(ChannelRepository, ChannelRepositoryPort):
    async def get_by_id(self, channel_id: str, workspace_id: str) -> Channel | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.id == channel_id)
                .where(ChannelModel.workspace_id == workspace_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def list_by_workspace(self, workspace_id: str) -> list[Channel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel).where(ChannelModel.workspace_id == workspace_id)
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, channel: Channel) -> Channel:
        async with AsyncSessionLocal() as session:
            model = self._to_model(channel)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def update(self, channel: Channel) -> Channel:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.id == channel.id)
                .where(ChannelModel.workspace_id == channel.workspace_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                model = self._to_model(channel)
                session.add(model)
            else:
                model.provider = channel.provider
                model.group = channel.group
                model.config = channel.config
                model.is_active = channel.is_active
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def get_active_channels(self, workspace_id: str) -> list[Channel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.workspace_id == workspace_id)
                .where(ChannelModel.is_active.is_(True))
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    @staticmethod
    def _to_domain(model: ChannelModel) -> Channel:
        return Channel(
            id=model.id,
            workspace_id=model.workspace_id,
            provider=model.provider,
            group=model.group,
            config=model.config,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_model(channel: Channel) -> ChannelModel:
        return ChannelModel(
            id=channel.id,
            workspace_id=channel.workspace_id,
            provider=channel.provider,
            group=channel.group,
            config=channel.config,
            is_active=channel.is_active,
        )
