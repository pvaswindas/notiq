from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.workspace import Workspace


class WorkspaceRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        pass
