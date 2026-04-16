from redis import Redis

from src.bootstrap.settings import settings
from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limiter import RateLimiterPort


class RedisDeliveryRateLimiter(RateLimiterPort):
    """Redis-backed fixed-window limiter for notification delivery safety."""

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

    _BATCH_SCRIPT = """
for i = 1, #KEYS do
  local current = tonumber(redis.call('GET', KEYS[i]) or '0')
  local limit = tonumber(ARGV[((i - 1) * 2) + 1])
  if current >= limit then
    return i
  end
end

for i = 1, #KEYS do
  local window_seconds = tonumber(ARGV[((i - 1) * 2) + 2])
  local current = redis.call('INCR', KEYS[i])
  if current == 1 then
    redis.call('EXPIRE', KEYS[i], window_seconds)
  end
end

return 0
"""

    def __init__(self, redis_client: Redis | None = None) -> None:
        self._redis = redis_client or Redis.from_url(settings.redis_url)
        self._allow_script = self._redis.register_script(self._SCRIPT)
        self._allow_many_script = self._redis.register_script(self._BATCH_SCRIPT)

    def allow(self, config: RateLimitConfig) -> bool:
        redis_key = f"rate_limit:{config.scope}:{config.key}"
        allowed = self._allow_script(keys=[redis_key], args=[config.window_seconds, config.limit])
        return bool(int(allowed))

    def allow_many(self, configs: list[RateLimitConfig]) -> tuple[bool, int | None]:
        if not configs:
            return True, None

        redis_keys = [f"rate_limit:{config.scope}:{config.key}" for config in configs]
        args: list[int] = []
        for config in configs:
            args.extend([config.limit, config.window_seconds])

        violated_position = int(self._allow_many_script(keys=redis_keys, args=args))
        if violated_position == 0:
            return True, None
        return False, violated_position - 1
