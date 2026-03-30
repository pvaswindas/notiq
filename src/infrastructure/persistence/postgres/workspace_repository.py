from sqlalchemy import select

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import WorkspaceModel
from src.modules.notifications.domain.entities.workspace import Workspace
from src.modules.notifications.ports.workspace_repository_port import WorkspaceRepositoryPort


class PostgresWorkspaceRepository(WorkspaceRepositoryPort):
    """Postgres adapter for workspace tenant-state retrieval."""

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Fetch a workspace by id from Postgres."""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkspaceModel).where(WorkspaceModel.workspace_id == workspace_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return Workspace(
                workspace_id=model.workspace_id,
                name=model.name,
                is_active=model.is_active,
                created_at=model.created_at,
            )
