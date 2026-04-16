from dataclasses import dataclass
from datetime import datetime, timezone

from src.bootstrap.settings import Settings
from src.domain.rate_limit.entities import RateLimitConfig
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob
from src.ports.rate_limit_config_repository import RateLimitConfigRepository
from src.ports.rate_limiter import RateLimiterPort


@dataclass(slots=True, frozen=True)
class DeliveryRateLimitRule:
    """Concrete rate-limit rule to enforce for one delivery attempt."""

    scope: str
    key: str
    limit: int
    window_seconds: int


@dataclass(slots=True, frozen=True)
class DeliveryRateLimitResult:
    """Outcome of evaluating rate-limit rules for a delivery job."""

    allowed: bool
    violated_scope: str | None = None
    violated_key: str | None = None
    limit: int | None = None
    window_seconds: int | None = None


class DeliverySafetyService:
    """Resolve and enforce delivery safety policies before provider send."""

    def __init__(
        self,
        rate_limiter: RateLimiterPort,
        settings: Settings,
        rate_limit_config_repository: RateLimitConfigRepository | None = None,
    ) -> None:
        self._rate_limiter = rate_limiter
        self._settings = settings
        self._rate_limit_config_repository = rate_limit_config_repository

    async def check_rate_limit(self, job: DeliveryJob) -> DeliveryRateLimitResult:
        """Check workspace and optional channel limits for a job attempt."""

        rules = await self._build_rules(job)
        if not rules:
            return DeliveryRateLimitResult(allowed=True)

        now = datetime.now(timezone.utc)
        configs = [
            RateLimitConfig(
                scope=rule.scope,
                key=f"{rule.key}:{int(now.timestamp()) // rule.window_seconds}",
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )
            for rule in rules
        ]
        allowed, violated_index = self._rate_limiter.allow_many(configs)
        if not allowed and violated_index is not None:
            violated_rule = rules[violated_index]
            return DeliveryRateLimitResult(
                allowed=False,
                violated_scope=violated_rule.scope,
                violated_key=violated_rule.key,
                limit=violated_rule.limit,
                window_seconds=violated_rule.window_seconds,
            )

        return DeliveryRateLimitResult(allowed=True)

    async def _build_rules(self, job: DeliveryJob) -> list[DeliveryRateLimitRule]:
        configured_limits: dict[tuple[str, str], RateLimitConfig] = {}
        if self._rate_limit_config_repository is not None:
            for config in await self._rate_limit_config_repository.list_by_workspace(job.workspace_id):
                config_key = (config.scope, config.key)
                existing_config = configured_limits.get(config_key)
                if existing_config is None or (
                    existing_config.workspace_id is None and config.workspace_id == job.workspace_id
                ):
                    configured_limits[config_key] = config

        workspace_config = configured_limits.get(("tenant", job.workspace_id))
        workspace_rule = DeliveryRateLimitRule(
            scope="tenant",
            key=job.workspace_id,
            limit=workspace_config.limit
            if workspace_config is not None
            else self._settings.delivery_workspace_rate_limit_per_minute,
            window_seconds=workspace_config.window_seconds
            if workspace_config is not None
            else self._settings.delivery_rate_limit_window_seconds,
        )

        rules = [workspace_rule]

        channel_config = configured_limits.get(("channel", job.channel_id))
        channel_limit = (
            channel_config.limit if channel_config is not None else self._settings.delivery_channel_rate_limit_per_minute
        )
        if channel_limit > 0:
            rules.append(
                DeliveryRateLimitRule(
                    scope="channel",
                    key=f"{job.workspace_id}:{job.channel_id}",
                    limit=channel_limit,
                    window_seconds=channel_config.window_seconds
                    if channel_config is not None
                    else self._settings.delivery_rate_limit_window_seconds,
                )
            )

        return rules
