from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob


class DeliveryJobRepositoryPort(ABC):
    @abstractmethod
    async def save(self, job: DeliveryJob) -> None:
        pass

    @abstractmethod
    async def update(self, job: DeliveryJob) -> None:
        pass

    @abstractmethod
    async def claim_due_jobs(self, worker_id: str, limit: int, lease_seconds: int) -> list[DeliveryJob]:
        pass
