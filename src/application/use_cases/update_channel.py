from dataclasses import dataclass
from typing import Any

from src.domain.entities.channel import Channel
from src.ports.channel_repository import ChannelRepository


@dataclass(slots=True, frozen=True)
class UpdateChannelInput:
    channel_id: str
    workspace_id: str
    provider: str
    config: dict[str, Any] | None = None
    group: str | None = None
    is_active: bool | None = None


class UpdateChannelUseCase:
    def __init__(self, channel_repository: ChannelRepository) -> None:
        self._channel_repository = channel_repository

    async def execute(self, dto: UpdateChannelInput) -> Channel:
        channel_id = dto.channel_id.strip()
        workspace_id = dto.workspace_id.strip()
        provider = dto.provider.strip()

        if not channel_id:
            raise ValueError("channel_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")
        if not provider:
            raise ValueError("provider is required")

        current_channel = await self._channel_repository.get_by_id(channel_id, workspace_id)
        if current_channel is None:
            raise LookupError("channel not found")

        updated_channel = Channel(
            id=current_channel.id,
            workspace_id=current_channel.workspace_id,
            provider=provider,
            group=dto.group,
            config=dto.config or {},
            is_active=current_channel.is_active if dto.is_active is None else dto.is_active,
        )

        return await self._channel_repository.update(updated_channel)
