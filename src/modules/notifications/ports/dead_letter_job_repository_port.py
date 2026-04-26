from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.dead_letter_job import DeadLetterJob


class DeadLetterJobRepositoryPort(ABC):
    """Port for persisting and querying terminal delivery failures (DLQ)."""

    @abstractmethod
    async def save(self, job: DeadLetterJob) -> None:
        """Persist a new DLQ entry for a permanently failed delivery job."""

    @abstractmethod
    async def get_by_id(self, dead_letter_job_id: str, workspace_id: str) -> DeadLetterJob | None:
        """Return a DLQ entry by id scoped to a workspace."""

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str, limit: int, offset: int) -> list[DeadLetterJob]:
        """List DLQ entries for a workspace ordered by newest first."""

