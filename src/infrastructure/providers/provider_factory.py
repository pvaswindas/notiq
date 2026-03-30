from src.adapters.providers.telegram_notifier import TelegramNotifier
from src.ports.provider import NotificationProviderPort
from src.ports.provider_factory import ProviderFactoryPort


class ProviderFactory(ProviderFactoryPort):
    def __init__(self, providers: dict[str, NotificationProviderPort] | None = None) -> None:
        self._providers = providers or {"telegram": TelegramNotifier()}

    def get(self, provider_name: str) -> NotificationProviderPort:
        key = provider_name.strip().lower()
        provider = self._providers.get(key)
        if provider is None:
            raise ValueError(f"unsupported provider: {provider_name}")
        return provider
