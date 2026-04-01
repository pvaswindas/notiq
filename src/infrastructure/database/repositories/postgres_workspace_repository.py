from sqlalchemy import select

from src.domain.entities.workspace import Workspace
from src.infrastructure.database.models import WorkspaceModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.workspace_repository import WorkspaceRepository


class PostgresWorkspaceRepository(WorkspaceRepository):
    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        async with AsyncSessionLocal() as session:
            model = await session.get(WorkspaceModel, workspace_id)
            if model is None:
                return None
            return self._to_domain(model)

    async def list_by_workspace(self, workspace_id: str) -> list[Workspace]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(WorkspaceModel).where(WorkspaceModel.id == workspace_id))
            return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, workspace: Workspace) -> Workspace:
        async with AsyncSessionLocal() as session:
            model = WorkspaceModel(id=workspace.id, name=workspace.name, created_at=workspace.created_at)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def update(self, workspace: Workspace) -> Workspace:
        async with AsyncSessionLocal() as session:
            model = await session.get(WorkspaceModel, workspace.id)
            if model is None:
                model = WorkspaceModel(id=workspace.id, name=workspace.name, created_at=workspace.created_at)
                session.add(model)
            else:
                model.name = workspace.name
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    @staticmethod
    def _to_domain(model: WorkspaceModel) -> Workspace:
        return Workspace(id=model.id, name=model.name, created_at=model.created_at)
