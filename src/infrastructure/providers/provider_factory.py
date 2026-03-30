from src.adapters.providers.telegram_notifier import TelegramNotifier
from src.ports.provider import NotificationProviderPort
from src.ports.provider_factory import ProviderFactoryPort


class ProviderFactory(ProviderFactoryPort):
    """Resolve legacy notification provider adapters by provider key.

    Architectural role:
    - Infrastructure adapter for compatibility path provider selection.
    """

    def __init__(self, providers: dict[str, NotificationProviderPort] | None = None) -> None:
        """Initialize provider map with default built-in adapters.

        Args:
            providers: Optional provider-name to adapter mapping. When omitted,
                a default Telegram provider mapping is used.
        """

        self._providers = providers or {"telegram": TelegramNotifier()}

    def get(self, provider_name: str) -> NotificationProviderPort:
        """Return provider adapter by normalized provider name.

        Args:
            provider_name: Provider key supplied by channel configuration.

        Returns:
            NotificationProviderPort: Matching provider adapter.

        Raises:
            ValueError: If provider key is not registered.
        """

        key = provider_name.strip().lower()
        provider = self._providers.get(key)
        if provider is None:
            raise ValueError(f"unsupported provider: {provider_name}")
        return provider
