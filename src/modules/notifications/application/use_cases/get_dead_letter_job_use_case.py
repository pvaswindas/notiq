from dataclasses import dataclass

from src.modules.notifications.domain.entities.dead_letter_job import DeadLetterJob
from src.modules.notifications.ports.dead_letter_job_repository_port import DeadLetterJobRepositoryPort


@dataclass(slots=True, frozen=True)
class GetDeadLetterJobCommand:
    dead_letter_job_id: str
    workspace_id: str


class GetDeadLetterJobUseCase:
    """Fetch a DLQ entry by id with tenant scoping."""

    def __init__(self, dead_letter_job_repository: DeadLetterJobRepositoryPort) -> None:
        self._dead_letter_job_repository = dead_letter_job_repository

    async def execute(self, command: GetDeadLetterJobCommand) -> DeadLetterJob:
        if not command.dead_letter_job_id:
            raise ValueError("dead_letter_job_id is required")
        if not command.workspace_id:
            raise ValueError("workspace_id is required")
        job = await self._dead_letter_job_repository.get_by_id(
            dead_letter_job_id=command.dead_letter_job_id,
            workspace_id=command.workspace_id,
        )
        if job is None:
            raise LookupError(f"dead letter job not found: {command.dead_letter_job_id}")
        return job

