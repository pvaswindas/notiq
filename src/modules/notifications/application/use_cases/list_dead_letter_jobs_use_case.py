from dataclasses import dataclass

from src.modules.notifications.domain.entities.dead_letter_job import DeadLetterJob
from src.modules.notifications.ports.dead_letter_job_repository_port import DeadLetterJobRepositoryPort


@dataclass(slots=True, frozen=True)
class ListDeadLetterJobsCommand:
    workspace_id: str
    limit: int = 100
    offset: int = 0


class ListDeadLetterJobsUseCase:
    """List DLQ entries for a workspace."""

    def __init__(self, dead_letter_job_repository: DeadLetterJobRepositoryPort) -> None:
        self._dead_letter_job_repository = dead_letter_job_repository

    async def execute(self, command: ListDeadLetterJobsCommand) -> list[DeadLetterJob]:
        if not command.workspace_id:
            raise ValueError("workspace_id is required")
        return await self._dead_letter_job_repository.list_by_workspace(
            workspace_id=command.workspace_id,
            limit=command.limit,
            offset=command.offset,
        )

