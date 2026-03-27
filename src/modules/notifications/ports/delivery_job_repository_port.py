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
        """
        Purpose:
        - Persist a newly created delivery job.

        Inputs:
        - job: DeliveryJob with initial lifecycle metadata.

        Outputs:
        - None.
        """

    @abstractmethod
    async def update(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Persist updates to an existing delivery job.

        Inputs:
        - job: DeliveryJob containing a new lifecycle state.

        Outputs:
        - None.
        """

    @abstractmethod
    async def get_pending_jobs(self, limit: int) -> list[DeliveryJob]:
        """
        Purpose:
        - Return jobs currently eligible for worker execution.

        Inputs:
        - limit: Maximum number of jobs to return.

        Outputs:
        - list[DeliveryJob] constrained by limit.
        """
