"""Legacy compatibility ports exported for composition roots."""

from src.ports.channel_repository import ChannelRepository
from src.ports.channel_repository_port import ChannelRepositoryPort
from src.ports.admin_repository import AdminRepository
from src.ports.api_key_repository import ApiKeyRepository
from src.ports.audit_log_repository import AuditLogRepository
from src.ports.permission_repository import PermissionRepository
from src.ports.rate_limit_config_repository import RateLimitConfigRepository
from src.ports.rate_limit_config_repository import RateLimitConfigRepositoryPort
from src.ports.rate_limiter import RateLimiterPort
from src.ports.role_repository import RoleRepository
from src.ports.workspace_repository import WorkspaceRepository

__all__ = [
    "AdminRepository",
    "ApiKeyRepository",
    "AuditLogRepository",
    "ChannelRepository",
    "ChannelRepositoryPort",
    "PermissionRepository",
    "RateLimitConfigRepository",
    "RateLimitConfigRepositoryPort",
    "RateLimiterPort",
    "RoleRepository",
    "WorkspaceRepository",
]
