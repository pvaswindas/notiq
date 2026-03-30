from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class SenderRegistry(SenderRegistryPort):
    """In-memory registry that maps provider keys to sender adapters."""

    def __init__(self, senders: dict[str, NotificationSenderPort]) -> None:
        """Initialize provider sender map used at delivery execution time."""

        self._senders = senders

    def resolve(self, provider_key: str) -> NotificationSenderPort:
        """Resolve sender adapter by provider key.

        Raises:
        - ValueError: If no sender is registered for the provider.
        """

        sender = self._senders.get(provider_key)
        if sender is None:
            raise ValueError(f"unsupported provider: {provider_key}")
        return sender
