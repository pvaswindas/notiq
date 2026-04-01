from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from src.domain.entities.channel import Channel
from src.ports.channel_repository import ChannelRepository
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class CreateChannelInput:
    workspace_id: str
    provider: str
    config: dict[str, Any] | None = None
    group: str | None = None
    is_active: bool | None = None


class CreateChannelUseCase:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self._channel_repository = channel_repository
        self._workspace_repository = workspace_repository

    async def execute(self, dto: CreateChannelInput) -> Channel:
        workspace_id = dto.workspace_id.strip()
        if not workspace_id:
            raise ValueError("workspace_id is required")

        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError("workspace not found")

        provider = dto.provider.strip()
        if not provider:
            raise ValueError("provider is required")

        channel = Channel(
            id=f"ch_{uuid4().hex[:24]}",
            workspace_id=workspace_id,
            provider=provider,
            group=dto.group,
            config=dto.config or {},
            is_active=True if dto.is_active is None else dto.is_active,
        )
        return await self._channel_repository.save(channel)
