from dataclasses import dataclass

from src.domain.entities.workspace import Workspace
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class GetWorkspaceInput:
    id: str


class GetWorkspaceUseCase:
    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, dto: GetWorkspaceInput) -> Workspace | None:
        workspace_id = dto.id.strip()
        if not workspace_id:
            raise ValueError("id is required")
        return await self._workspace_repository.get_by_id(workspace_id)
