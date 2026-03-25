from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class SenderRegistry(SenderRegistryPort):
    """
    Purpose:
    - Provide application-level provider routing for notification senders.

    Responsibilities:
    - Map provider keys to notification sender implementations.
    - Resolve the sender contract used by delivery orchestration.

    Inputs:
    - senders: dict[str, NotificationSenderPort]

    Outputs:
    - NotificationSenderPort from resolve.

    Constraints:
    - Must remain infrastructure-agnostic and contain no delivery logic.
    """

    def __init__(self, senders: dict[str, NotificationSenderPort]) -> None:
        """
        Purpose:
        - Initialize sender registry with injected sender implementations.

        Responsibilities:
        - Store sender mapping for provider lookup.

        Inputs:
        - senders: dict[str, NotificationSenderPort]

        Outputs:
        - None

        Constraints:
        - Mapping keys must match channel provider_key values.
        """

        self._senders = senders

    def resolve(self, provider_key: str) -> NotificationSenderPort:
        """
        Purpose:
        - Resolve sender implementation for a provider key.

        Responsibilities:
        - Return matching sender from registry mapping.

        Inputs:
        - provider_key: str

        Outputs:
        - NotificationSenderPort

        Constraints:
        - Raises ValueError when provider key is unsupported.
        """

        sender = self._senders.get(provider_key)
        if sender is None:
            raise ValueError(f"unsupported provider: {provider_key}")
        return sender
