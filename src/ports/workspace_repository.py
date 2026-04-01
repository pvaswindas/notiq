from abc import ABC, abstractmethod

from src.domain.entities.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[Workspace]:
        ...

    @abstractmethod
    async def list_all(self) -> list[Workspace]:
        ...

    @abstractmethod
    async def save(self, workspace: Workspace) -> Workspace:
        ...

    @abstractmethod
    async def update(self, workspace: Workspace) -> Workspace:
        ...
