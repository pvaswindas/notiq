"""Legacy compatibility ports exported for composition roots."""

from src.ports.channel_repository import ChannelRepository
from src.ports.channel_repository_port import ChannelRepositoryPort
from src.ports.event_queue_port import EventQueuePort
from src.ports.idempotency_store import IdempotencyStorePort
from src.ports.rate_limit_config_repository import RateLimitConfigRepository
from src.ports.rate_limit_config_repository import RateLimitConfigRepositoryPort
from src.ports.rate_limiter import RateLimiterPort
from src.ports.workspace_repository import WorkspaceRepository

__all__ = [
    "ChannelRepository",
    "ChannelRepositoryPort",
    "EventQueuePort",
    "IdempotencyStorePort",
    "RateLimitConfigRepository",
    "RateLimitConfigRepositoryPort",
    "RateLimiterPort",
    "WorkspaceRepository",
]
