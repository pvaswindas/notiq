from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class DeliveryJobRepositoryPort(ABC):
    """Port for storing, updating, and claiming delivery jobs."""

    @abstractmethod
    async def save(self, job: DeliveryJob) -> None:
        """Persist a newly created delivery job."""

        pass

    @abstractmethod
    async def update(self, job: DeliveryJob) -> None:
        """Persist lifecycle updates for an existing delivery job."""

        pass

    @abstractmethod
    async def claim_due_jobs(self, worker_id: str, limit: int, lease_seconds: int) -> list[DeliveryJob]:
        """Atomically claim due jobs for processing under a worker lease."""

        pass
