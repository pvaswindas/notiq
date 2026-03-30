import asyncio
from typing import Any

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.infrastructure.celery_app import celery_app
from src.infrastructure.providers.provider_factory import ProviderFactory


@celery_app.task(name="notiq.send_notification", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def send_notification_task(self: Any, event_payload: dict[str, Any], channel_payload: dict[str, Any]) -> None:
    event = Event(**event_payload)
    channel = Channel(**channel_payload)
    provider_factory = ProviderFactory()
    provider = provider_factory.get(channel.provider)
    asyncio.run(provider.send(channel, event))
