import asyncio
from typing import Any

from src.application.services.idempotency import generate_idempotency_key
from src.bootstrap.settings import settings
from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.infrastructure.celery_app import celery_app
from src.infrastructure.providers.provider_factory import ProviderFactory
from src.infrastructure.redis.redis_idempotency_store import RedisIdempotencyStore


@celery_app.task(name="notiq.send_notification", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def send_notification_task(self: Any, event_payload: dict[str, Any], channel_payload: dict[str, Any]) -> None:
    event = Event(**event_payload)
    channel = Channel(**channel_payload)
    idempotency_key = generate_idempotency_key(event=event, channel=channel)
    idempotency_store = RedisIdempotencyStore()

    claimed = idempotency_store.save(idempotency_key, ttl_seconds=settings.idempotency_ttl_seconds)
    if not claimed:
        return

    provider_factory = ProviderFactory()
    provider = provider_factory.get(channel.provider)
    try:
        asyncio.run(provider.send(channel, event))
    except Exception:
        idempotency_store.delete(idempotency_key)
        raise
