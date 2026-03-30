from redis import Redis

from src.bootstrap.settings import settings
from src.ports.idempotency_store import IdempotencyStorePort


class RedisIdempotencyStore(IdempotencyStorePort):
    def __init__(self, redis_client: Redis | None = None) -> None:
        self._redis = redis_client or Redis.from_url(settings.redis_url)

    def exists(self, key: str) -> bool:
        return bool(self._redis.exists(key))

    def save(self, key: str, ttl_seconds: int) -> bool:
        return bool(self._redis.set(name=key, value="1", nx=True, ex=ttl_seconds))

    def delete(self, key: str) -> None:
        self._redis.delete(key)
