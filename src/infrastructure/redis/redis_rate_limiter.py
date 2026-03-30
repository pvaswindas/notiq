from redis import Redis

from src.bootstrap.settings import settings
from src.domain.rate_limit.entities import RateLimitConfig
from src.ports.rate_limiter import RateLimiterPort


class RedisRateLimiter(RateLimiterPort):
    """Redis-backed fixed-window limiter for legacy Celery task throttling.

    Purpose:
    - Enforce per-scope rate limits using atomic counter operations in Redis.

    Responsibilities:
    - Convert `RateLimitConfig` into deterministic Redis keys.
    - Evaluate allow/deny decision atomically through Lua script execution.

    Architectural role:
    - Infrastructure adapter implementing the `RateLimiterPort`.
    """

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
        """Initialize Redis connection and register atomic limiter script.

        Args:
            redis_client: Optional Redis client for tests or custom wiring.
        """

        self._redis = redis_client or Redis.from_url(settings.redis_url)
        self._allow_script = self._redis.register_script(self._SCRIPT)

    def allow(self, config: RateLimitConfig) -> bool:
        """Evaluate whether one task execution is permitted for a policy.

        Args:
            config: Scoped policy containing key, limit, and window.

        Returns:
            bool: True when execution is within limit; False when throttled.

        Internal flow:
        - Build key namespace from scope and policy key.
        - Run Lua script that increments counter and sets expiry atomically.
        - Compare current counter value with configured limit.

        Edge cases and constraints:
        - Redis I/O errors bubble to caller.
        - Key expiration defines fixed-window boundaries.
        """

        redis_key = f"rate_limit:{config.scope}:{config.key}"
        allowed = self._allow_script(keys=[redis_key], args=[config.window_seconds, config.limit])
        return bool(int(allowed))
