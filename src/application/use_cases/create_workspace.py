from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.entities.workspace import Workspace
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class CreateWorkspaceInput:
    name: str


class CreateWorkspaceUseCase:
    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, dto: CreateWorkspaceInput) -> Workspace:
        name = dto.name.strip()
        if not name:
            raise ValueError("name is required")

        workspace = Workspace(
            id=f"ws_{uuid4().hex[:24]}",
            name=name,
            created_at=datetime.now(timezone.utc),
        )
        return await self._workspace_repository.save(workspace)
