from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.ports.provider_factory import ProviderFactoryPort


class NotificationDispatcher:
    def __init__(self, provider_factory: ProviderFactoryPort) -> None:
        self._provider_factory = provider_factory

    async def dispatch(self, event: Event, channel: Channel) -> None:
        provider = self._provider_factory.get(channel.provider)
        await provider.send(channel, event)
