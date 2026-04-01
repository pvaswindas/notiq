from dataclasses import dataclass

from src.domain.entities.channel import Channel
from src.ports.channel_repository import ChannelRepository


@dataclass(slots=True, frozen=True)
class DisableChannelInput:
    channel_id: str
    workspace_id: str


class DisableChannelUseCase:
    def __init__(self, channel_repository: ChannelRepository) -> None:
        self._channel_repository = channel_repository

    async def execute(self, dto: DisableChannelInput) -> Channel:
        channel_id = dto.channel_id.strip()
        workspace_id = dto.workspace_id.strip()

        if not channel_id:
            raise ValueError("channel_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")

        current_channel = await self._channel_repository.get_by_id(channel_id, workspace_id)
        if current_channel is None:
            raise LookupError("channel not found")

        if not current_channel.is_active:
            return current_channel

        disabled_channel = Channel(
            id=current_channel.id,
            workspace_id=current_channel.workspace_id,
            provider=current_channel.provider,
            group=current_channel.group,
            config=current_channel.config,
            is_active=False,
        )
        return await self._channel_repository.update(disabled_channel)
