from dataclasses import dataclass

from src.domain.entities.channel import Channel
from src.ports.channel_repository import ChannelRepository
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class ListChannelsInput:
    workspace_id: str


class ListChannelsUseCase:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self._channel_repository = channel_repository
        self._workspace_repository = workspace_repository

    async def execute(self, dto: ListChannelsInput) -> list[Channel]:
        workspace_id = dto.workspace_id.strip()
        if not workspace_id:
            raise ValueError("workspace_id is required")

        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError("workspace not found")

        return await self._channel_repository.list_by_workspace(workspace_id)
