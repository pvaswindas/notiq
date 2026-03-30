from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


def utc_now() -> datetime:
    """Return current UTC timestamp for model defaults."""

    return datetime.now(timezone.utc)


class WorkspaceModel(Base):
    """ORM model for tenant workspace records."""

    __tablename__ = "workspaces"

    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class ProviderAccountModel(Base):
    """ORM model for provider credential/account configuration."""

    __tablename__ = "provider_accounts"

    provider_account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.workspace_id", ondelete="SET NULL"), nullable=True)
    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    credentials_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("workspace_id", "provider_key", "provider_account_id", name="uq_provider_account_workspace_provider_account"),
        Index("ix_provider_accounts_provider_key_active", "provider_key", "is_active"),
    )


class ChannelModel(Base):
    """ORM model for channel routing definitions."""

    __tablename__ = "channels"

    channel_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.workspace_id", ondelete="CASCADE"), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("provider_accounts.provider_account_id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("ix_channels_workspace_active", "workspace_id", "is_active"),
        Index("ix_channels_provider_account", "provider_account_id"),
    )


class DeliveryJobModel(Base):
    """ORM model for asynchronous delivery job lifecycle tracking."""

    __tablename__ = "delivery_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.workspace_id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("provider_accounts.provider_account_id", ondelete="SET NULL"),
        nullable=True,
    )
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processing_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("ix_delivery_jobs_status_retry", "status", "next_retry_at"),
        Index("ix_delivery_jobs_processing_expires", "processing_expires_at"),
        Index("ix_delivery_jobs_workspace_status", "workspace_id", "status"),
    )


class IdempotencyKeyModel(Base):
    """ORM model that stores claimed dedupe fingerprints."""

    __tablename__ = "idempotency_keys"

    dedupe_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
