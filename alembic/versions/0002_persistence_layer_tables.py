"""add persistence layer tables and tenant-safe columns

Revision ID: 0002_persistence_layer_tables
Revises: 0001_init
Create Date: 2026-03-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_persistence_layer_tables"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "workspaces"):
        op.create_table(
            "workspaces",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        if not _has_column(inspector, "workspaces", "id"):
            op.add_column("workspaces", sa.Column("id", sa.String(length=64), nullable=True))
            op.execute("UPDATE workspaces SET id = workspace_id WHERE id IS NULL")
            op.alter_column("workspaces", "id", nullable=False)

        if not _has_index(inspector, "workspaces", "ux_workspaces_id"):
            op.create_index("ux_workspaces_id", "workspaces", ["id"], unique=True)

    if not _has_table(inspector, "channels"):
        op.create_table(
            "channels",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("provider", sa.String(length=64), nullable=False),
            sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("group", sa.String(length=128), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        if not _has_column(inspector, "channels", "id"):
            op.add_column("channels", sa.Column("id", sa.String(length=64), nullable=True))
            op.execute("UPDATE channels SET id = channel_id WHERE id IS NULL")
            op.alter_column("channels", "id", nullable=False)

        if not _has_column(inspector, "channels", "provider"):
            op.add_column("channels", sa.Column("provider", sa.String(length=64), nullable=True))
            op.execute("UPDATE channels SET provider = provider_key WHERE provider IS NULL")
            op.alter_column("channels", "provider", nullable=False)

        if not _has_column(inspector, "channels", "config"):
            op.add_column(
                "channels",
                sa.Column(
                    "config",
                    postgresql.JSONB(astext_type=sa.Text()),
                    nullable=False,
                    server_default=sa.text("'{}'::jsonb"),
                ),
            )
            op.execute("UPDATE channels SET config = metadata WHERE config = '{}'::jsonb AND metadata IS NOT NULL")

        if not _has_column(inspector, "channels", "group"):
            op.add_column("channels", sa.Column("group", sa.String(length=128), nullable=True))

        if not _has_index(inspector, "channels", "ix_channels_workspace_is_active"):
            op.create_index("ix_channels_workspace_is_active", "channels", ["workspace_id", "is_active"])

        if not _has_index(inspector, "channels", "ix_channels_workspace_provider"):
            op.create_index("ix_channels_workspace_provider", "channels", ["workspace_id", "provider"])

    if not _has_table(inspector, "rate_limit_configs"):
        op.create_table(
            "rate_limit_configs",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=True),
            sa.Column("scope", sa.String(length=16), nullable=False),
            sa.Column("key", sa.String(length=128), nullable=False),
            sa.Column("limit", sa.Integer(), nullable=False),
            sa.Column("window_seconds", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_rate_limit_configs_workspace_scope", "rate_limit_configs", ["workspace_id", "scope"])
        op.create_index("ix_rate_limit_configs_scope_key", "rate_limit_configs", ["scope", "key"])

    if not _has_table(inspector, "event_logs"):
        op.create_table(
            "event_logs",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("event_type", sa.String(length=128), nullable=False),
            sa.Column("correlation_id", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_event_logs_workspace_created_at", "event_logs", ["workspace_id", "created_at"])
        op.create_index("ix_event_logs_workspace_correlation", "event_logs", ["workspace_id", "correlation_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "event_logs"):
        if _has_index(inspector, "event_logs", "ix_event_logs_workspace_correlation"):
            op.drop_index("ix_event_logs_workspace_correlation", table_name="event_logs")
        if _has_index(inspector, "event_logs", "ix_event_logs_workspace_created_at"):
            op.drop_index("ix_event_logs_workspace_created_at", table_name="event_logs")
        op.drop_table("event_logs")

    if _has_table(inspector, "rate_limit_configs"):
        if _has_index(inspector, "rate_limit_configs", "ix_rate_limit_configs_scope_key"):
            op.drop_index("ix_rate_limit_configs_scope_key", table_name="rate_limit_configs")
        if _has_index(inspector, "rate_limit_configs", "ix_rate_limit_configs_workspace_scope"):
            op.drop_index("ix_rate_limit_configs_workspace_scope", table_name="rate_limit_configs")
        op.drop_table("rate_limit_configs")

    if _has_table(inspector, "channels"):
        if _has_index(inspector, "channels", "ix_channels_workspace_provider"):
            op.drop_index("ix_channels_workspace_provider", table_name="channels")
        if _has_index(inspector, "channels", "ix_channels_workspace_is_active"):
            op.drop_index("ix_channels_workspace_is_active", table_name="channels")
        if _has_column(inspector, "channels", "group"):
            op.drop_column("channels", "group")
        if _has_column(inspector, "channels", "config"):
            op.drop_column("channels", "config")
        if _has_column(inspector, "channels", "provider"):
            op.drop_column("channels", "provider")
        if _has_column(inspector, "channels", "id"):
            op.drop_column("channels", "id")

    if _has_table(inspector, "workspaces"):
        if _has_index(inspector, "workspaces", "ux_workspaces_id"):
            op.drop_index("ux_workspaces_id", table_name="workspaces")
        if _has_column(inspector, "workspaces", "id"):
            op.drop_column("workspaces", "id")
