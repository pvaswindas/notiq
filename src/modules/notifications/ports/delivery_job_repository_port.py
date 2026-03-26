from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class DeliveryJobRepositoryPort(ABC):
    """
    Purpose:
    - Define persistence contract for delivery jobs.

    Responsibilities:
    - Store jobs.
    - Update job lifecycle state.
    - Retrieve pending jobs for worker polling.
    """

    @abstractmethod
    async def save(self, job: DeliveryJob) -> None:
        """Persist a newly created delivery job."""

    @abstractmethod
    async def update(self, job: DeliveryJob) -> None:
        """Persist updates to an existing delivery job."""

    @abstractmethod
    async def get_pending_jobs(self, limit: int) -> list[DeliveryJob]:
        """Return jobs ready for processing, up to the provided limit."""
