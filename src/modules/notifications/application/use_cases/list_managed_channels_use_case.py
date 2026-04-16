from dataclasses import dataclass

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.ports.channel_repository_port import ChannelRepositoryPort
from src.modules.notifications.ports.workspace_repository_port import WorkspaceRepositoryPort


@dataclass(slots=True, frozen=True)
class ListManagedChannelsCommand:
    workspace_id: str


class ListManagedChannelsUseCase:
    """List channels for a workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepositoryPort,
        channel_repository: ChannelRepositoryPort,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._channel_repository = channel_repository

    async def execute(self, command: ListManagedChannelsCommand) -> list[Channel]:
        workspace_id = command.workspace_id.strip()
        if not workspace_id:
            raise ValueError("workspace_id is required")

        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError("workspace not found")

        return await self._channel_repository.list_by_workspace(workspace_id)
