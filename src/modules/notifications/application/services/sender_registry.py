from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class SenderRegistry(SenderRegistryPort):
    def __init__(self, senders: dict[str, NotificationSenderPort]) -> None:
        self._senders = senders

    def resolve(self, provider_key: str) -> NotificationSenderPort:
        sender = self._senders.get(provider_key)
        if sender is None:
            raise ValueError(f"unsupported provider: {provider_key}")
        return sender
