from dataclasses import dataclass

from src.domain.entities.workspace import Workspace
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class ListWorkspacesInput:
    pass


class ListWorkspacesUseCase:
    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, dto: ListWorkspacesInput) -> list[Workspace]:
        _ = dto
        return await self._workspace_repository.list_all()
