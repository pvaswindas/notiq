from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.workspace import Workspace


class WorkspaceRepositoryPort(ABC):
    """Port for reading workspace tenant state."""

    @abstractmethod
    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Fetch workspace by identifier, or None when not found."""

        pass
