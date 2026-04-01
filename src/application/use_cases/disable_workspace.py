from dataclasses import dataclass

from src.application.services.audit_logger import AuditLogger
from src.domain.entities.workspace import Workspace
from src.ports.workspace_repository import WorkspaceRepository


@dataclass(slots=True, frozen=True)
class DisableWorkspaceInput:
    workspace_id: str
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class DisableWorkspaceUseCase:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._audit_logger = audit_logger

    async def execute(self, dto: DisableWorkspaceInput) -> Workspace:
        workspace_id = dto.workspace_id.strip()
        if not workspace_id:
            raise ValueError("workspace_id is required")

        current_workspace = await self._workspace_repository.get_by_id(workspace_id)
        if current_workspace is None:
            raise LookupError("workspace not found")

        if not current_workspace.is_active:
            return current_workspace

        disabled_workspace = await self._workspace_repository.set_active(workspace_id=workspace_id, is_active=False)
        if disabled_workspace is None:
            raise LookupError("workspace not found")

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=dto.actor_id,
                action="workspace.disable",
                resource="workspace",
                resource_id=disabled_workspace.id,
                before={
                    "id": current_workspace.id,
                    "name": current_workspace.name,
                    "is_active": current_workspace.is_active,
                },
                after={
                    "id": disabled_workspace.id,
                    "name": disabled_workspace.name,
                    "is_active": disabled_workspace.is_active,
                },
                metadata=dto.audit_metadata,
            )

        return disabled_workspace
