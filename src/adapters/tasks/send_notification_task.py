import asyncio
from dataclasses import dataclass
from typing import Any

from src.application.services.idempotency import generate_idempotency_key
from src.application.services.rate_limit_resolver import RateLimitResolver
from src.bootstrap.settings import settings
from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.infrastructure.config.in_memory_rate_limit_config_repo import InMemoryRateLimitConfigRepository
from src.infrastructure.celery_app import celery_app
from src.infrastructure.providers.provider_factory import ProviderFactory
from src.infrastructure.redis.redis_idempotency_store import RedisIdempotencyStore
from src.infrastructure.redis.redis_rate_limiter import RedisRateLimiter
from src.ports.idempotency_store import IdempotencyStorePort
from src.ports.provider_factory import ProviderFactoryPort
from src.ports.rate_limiter import RateLimiterPort


@dataclass(slots=True)
class SendNotificationTaskDependencies:
    idempotency_store: IdempotencyStorePort
    rate_limit_resolver: RateLimitResolver
    rate_limiter: RateLimiterPort
    provider_factory: ProviderFactoryPort


def _build_dependencies() -> SendNotificationTaskDependencies:
    config_repository = InMemoryRateLimitConfigRepository()
    return SendNotificationTaskDependencies(
        idempotency_store=RedisIdempotencyStore(),
        rate_limit_resolver=RateLimitResolver(config_repository=config_repository),
        rate_limiter=RedisRateLimiter(),
        provider_factory=ProviderFactory(),
    )


_DEPENDENCIES = _build_dependencies()


@celery_app.task(name="notiq.send_notification", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def send_notification_task(self: Any, event_payload: dict[str, Any], channel_payload: dict[str, Any]) -> None:
    """Execute one legacy provider delivery task for an event-channel pair.

    Purpose:
    - Compatibility Celery task that performs idempotent provider delivery.

    Args:
        self: Celery task instance (unused directly, required by bind=True).
        event_payload: Serialized event dictionary from enqueue step.
        channel_payload: Serialized channel dictionary from enqueue step.

    Returns:
        None.

    Internal flow:
    - Rehydrate domain objects from payload dictionaries.
    - Compute and claim Redis-backed idempotency key.
    - Resolve provider implementation from provider factory.
    - Execute async provider send inside task process.

    Edge cases and constraints:
    - Duplicate idempotency claims return early without provider call.
    - On provider failure, idempotency key is released before raising so task
      retry can re-attempt delivery.
    """

    event = Event(**event_payload)
    channel = Channel(**channel_payload)
    idempotency_key = generate_idempotency_key(event=event, channel=channel)

    claimed = _DEPENDENCIES.idempotency_store.save(idempotency_key, ttl_seconds=settings.idempotency_ttl_seconds)
    if not claimed:
        return

    rate_limit_config = _DEPENDENCIES.rate_limit_resolver.resolve(event=event, channel=channel)
    if not _DEPENDENCIES.rate_limiter.allow(rate_limit_config):
        _DEPENDENCIES.idempotency_store.delete(idempotency_key)
        self.apply_async(kwargs={"event_payload": event_payload, "channel_payload": channel_payload}, countdown=1)
        return

    provider = _DEPENDENCIES.provider_factory.get(channel.provider)
    try:
        asyncio.run(provider.send(channel, event))
    except Exception:
        _DEPENDENCIES.idempotency_store.delete(idempotency_key)
        raise
