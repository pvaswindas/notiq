from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob
from src.modules.notifications.domain.entities.provider_account import ProviderAccount


class NotificationSenderPort(ABC):
    @abstractmethod
    async def send(self, job: DeliveryJob, provider_account: ProviderAccount) -> None:
        pass
