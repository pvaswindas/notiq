from abc import ABC, abstractmethod

from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort


class SenderRegistryPort(ABC):
    """
    Purpose:
    - Define provider sender lookup contract.

    Responsibilities:
    - Resolve notification sender by provider key.
    """

    @abstractmethod
    def resolve(self, provider_key: str) -> NotificationSenderPort:
        """
        Purpose:
        - Resolve the outbound sender implementation for a provider key.

        Inputs:
        - provider_key: Logical provider identifier from channel configuration.

        Outputs:
        - NotificationSenderPort implementation for provider delivery calls.
        """
