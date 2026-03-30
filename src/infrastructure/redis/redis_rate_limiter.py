from redis import Redis

from src.bootstrap.settings import settings
from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limiter import RateLimiterPort


class RedisRateLimiter(RateLimiterPort):
    _SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end
if current > tonumber(ARGV[2]) then
  return 0
end
return 1
"""

    def __init__(self, redis_client: Redis | None = None) -> None:
        self._redis = redis_client or Redis.from_url(settings.redis_url)
        self._allow_script = self._redis.register_script(self._SCRIPT)

    def allow(self, config: RateLimitConfig) -> bool:
        redis_key = f"rate_limit:{config.scope}:{config.key}"
        allowed = self._allow_script(keys=[redis_key], args=[config.window_seconds, config.limit])
        return bool(int(allowed))
