from abc import ABC, abstractmethod

from src.ports.provider import NotificationProviderPort


class ProviderFactoryPort(ABC):
    @abstractmethod
    def get(self, provider_name: str) -> NotificationProviderPort:
        ...
