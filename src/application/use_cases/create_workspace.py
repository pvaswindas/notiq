from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from src.application.services.audit_logger import AuditLogger
from src.domain.entities.workspace import Workspace
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class CreateWorkspaceInput:
    name: str
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class CreateWorkspaceUseCase:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._audit_logger = audit_logger

    async def execute(self, dto: CreateWorkspaceInput) -> Workspace:
        name = dto.name.strip()
        if not name:
            raise ValueError("name is required")

        workspace = Workspace(
            id=f"ws_{uuid4().hex[:24]}",
            name=name,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
        created_workspace = await self._workspace_repository.save(workspace)

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=dto.actor_id,
                action="workspace.create",
                resource="workspace",
                resource_id=created_workspace.id,
                before=None,
                after={
                    "id": created_workspace.id,
                    "name": created_workspace.name,
                    "is_active": created_workspace.is_active,
                },
                metadata=dto.audit_metadata,
            )

        return created_workspace
