from dataclasses import dataclass

from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort
from src.modules.notifications.ports.workspace_repository_port import WorkspaceRepositoryPort


@dataclass(slots=True, frozen=True)
class ListProviderAccountsCommand:
    workspace_id: str


class ListProviderAccountsUseCase:
    """List provider accounts for one workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepositoryPort,
        provider_account_repository: ProviderAccountRepositoryPort,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._provider_account_repository = provider_account_repository

    async def execute(self, command: ListProviderAccountsCommand) -> list[ProviderAccount]:
        workspace_id = command.workspace_id.strip()
        if not workspace_id:
            raise ValueError("workspace_id is required")

        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError("workspace not found")

        return await self._provider_account_repository.list_by_workspace(workspace_id)
