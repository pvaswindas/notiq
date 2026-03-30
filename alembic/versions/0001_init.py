"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-03-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables, constraints, and indexes for Notiq persistence."""

    op.create_table(
        "workspaces",
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("workspace_id"),
    )

    op.create_table(
        "provider_accounts",
        sa.Column("provider_account_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("provider_key", sa.String(length=64), nullable=False),
        sa.Column("credentials_ref", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.workspace_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("provider_account_id"),
    )
    op.create_index("ix_provider_accounts_provider_key_active", "provider_accounts", ["provider_key", "is_active"])

    op.create_table(
        "channels",
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("provider_key", sa.String(length=64), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("provider_account_id", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["provider_account_id"], ["provider_accounts.provider_account_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.workspace_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("channel_id"),
    )
    op.create_index("ix_channels_workspace_active", "channels", ["workspace_id", "is_active"])
    op.create_index("ix_channels_provider_account", "channels", ["provider_account_id"])

    op.create_table(
        "delivery_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("provider_key", sa.String(length=64), nullable=False),
        sa.Column("provider_account_id", sa.String(length=64), nullable=True),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_owner", sa.String(length=128), nullable=True),
        sa.Column("processing_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.channel_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_account_id"], ["provider_accounts.provider_account_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.workspace_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
        sa.UniqueConstraint("dedupe_key"),
    )
    op.create_index("ix_delivery_jobs_status_retry", "delivery_jobs", ["status", "next_retry_at"])
    op.create_index("ix_delivery_jobs_processing_expires", "delivery_jobs", ["processing_expires_at"])
    op.create_index("ix_delivery_jobs_workspace_status", "delivery_jobs", ["workspace_id", "status"])

    op.create_table(
        "idempotency_keys",
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("dedupe_key"),
    )


def downgrade() -> None:
    """Drop all schema objects created by the initial migration."""

    op.drop_table("idempotency_keys")
    op.drop_index("ix_delivery_jobs_workspace_status", table_name="delivery_jobs")
    op.drop_index("ix_delivery_jobs_processing_expires", table_name="delivery_jobs")
    op.drop_index("ix_delivery_jobs_status_retry", table_name="delivery_jobs")
    op.drop_table("delivery_jobs")
    op.drop_index("ix_channels_provider_account", table_name="channels")
    op.drop_index("ix_channels_workspace_active", table_name="channels")
    op.drop_table("channels")
    op.drop_index("ix_provider_accounts_provider_key_active", table_name="provider_accounts")
    op.drop_table("provider_accounts")
    op.drop_table("workspaces")
