from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column("workspace_id", String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class ChannelModel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column("channel_id", String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.workspace_id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column("provider_key", String(64), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    config: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    provider_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    group: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("ix_channels_workspace_is_active", "workspace_id", "is_active"),
        Index("ix_channels_workspace_provider", "workspace_id", "provider"),
    )


class RateLimitConfigModel(Base):
    __tablename__ = "rate_limit_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_rate_limit_configs_workspace_scope", "workspace_id", "scope"),
        Index("ix_rate_limit_configs_scope_key", "scope", "key"),
    )


class EventLogModel(Base):
    __tablename__ = "event_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_event_logs_workspace_created_at", "workspace_id", "created_at"),
        Index("ix_event_logs_workspace_correlation", "workspace_id", "correlation_id"),
    )


class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.workspace_id", ondelete="CASCADE"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_api_keys_workspace_id", "workspace_id"),
        Index("ux_api_keys_key_hash", "key_hash", unique=True),
    )


class AdminModel(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ux_admins_email", "email", unique=True),
    )


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ux_roles_name", "name", unique=True),
    )


class PermissionModel(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ux_permissions_name", "name", unique=True),
    )


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[str] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        Index("ix_role_permissions_permission_id", "permission_id"),
    )


class AdminRoleModel(Base):
    __tablename__ = "admin_roles"

    admin_id: Mapped[str] = mapped_column(
        ForeignKey("admins.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        Index("ix_admin_roles_role_id", "role_id"),
    )
