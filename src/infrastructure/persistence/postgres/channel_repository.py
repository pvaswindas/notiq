from sqlalchemy import select

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import ChannelModel
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.ports.channel_repository_port import ChannelRepositoryPort


class PostgresChannelRepository(ChannelRepositoryPort):
    """Postgres adapter for channel lookups used during routing."""

    async def create(self, channel: Channel) -> Channel:
        """Persist a new channel."""

        async with AsyncSessionLocal() as session:
            model = self._to_model(channel)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def get_by_id(self, channel_id: str, workspace_id: str) -> Channel | None:
        """Fetch one channel by id and workspace scope."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.channel_id == channel_id)
                .where(ChannelModel.workspace_id == workspace_id)
            )
            return self._to_domain(result.scalar_one_or_none())

    async def list_by_workspace(self, workspace_id: str) -> list[Channel]:
        """List all channels for one workspace."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.workspace_id == workspace_id)
                .order_by(ChannelModel.created_at.desc())
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        """Return active channels for a workspace from the channels table."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.workspace_id == workspace_id)
                .where(ChannelModel.is_active.is_(True))
            )
            return [self._to_domain(model) for model in result.scalars().all()]

    async def update(self, channel: Channel) -> Channel:
        """Persist changes to an existing channel."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.channel_id == channel.channel_id)
                .where(ChannelModel.workspace_id == channel.workspace_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise LookupError("channel not found")

            model.provider_key = channel.provider_key
            model.destination = channel.destination
            model.provider_account_id = channel.provider_account_id
            model.is_active = channel.is_active
            model.metadata_json = dict(channel.metadata)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def find_by_route(
        self,
        workspace_id: str,
        provider_key: str,
        provider_account_id: str,
        destination: str,
    ) -> Channel | None:
        """Find an existing channel using the route tuple."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChannelModel)
                .where(ChannelModel.workspace_id == workspace_id)
                .where(ChannelModel.provider_key == provider_key)
                .where(ChannelModel.provider_account_id == provider_account_id)
                .where(ChannelModel.destination == destination)
            )
            return self._to_domain(result.scalar_one_or_none())

    @staticmethod
    def _to_domain(model: ChannelModel | None) -> Channel | None:
        if model is None:
            return None
        return Channel(
            channel_id=model.channel_id,
            workspace_id=model.workspace_id,
            provider_key=model.provider_key,
            destination=model.destination,
            provider_account_id=model.provider_account_id,
            is_active=model.is_active,
            metadata=dict(model.metadata_json or {}),
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(channel: Channel) -> ChannelModel:
        return ChannelModel(
            channel_id=channel.channel_id,
            workspace_id=channel.workspace_id,
            provider_key=channel.provider_key,
            destination=channel.destination,
            provider_account_id=channel.provider_account_id,
            is_active=channel.is_active,
            metadata_json=dict(channel.metadata),
            created_at=channel.created_at,
        )
