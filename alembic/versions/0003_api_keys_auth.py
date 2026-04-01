"""add api keys table for workspace authentication

Revision ID: 0003_api_keys_auth
Revises: 0002_persistence_layer_tables
Create Date: 2026-04-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_api_keys_auth"
down_revision: Union[str, None] = "0002_persistence_layer_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "api_keys"):
        op.create_table(
            "api_keys",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("key_hash", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.workspace_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index(inspector, "api_keys", "ix_api_keys_workspace_id"):
        op.create_index("ix_api_keys_workspace_id", "api_keys", ["workspace_id"])

    if not _has_index(inspector, "api_keys", "ux_api_keys_key_hash"):
        op.create_index("ux_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "api_keys"):
        if _has_index(inspector, "api_keys", "ux_api_keys_key_hash"):
            op.drop_index("ux_api_keys_key_hash", table_name="api_keys")
        if _has_index(inspector, "api_keys", "ix_api_keys_workspace_id"):
            op.drop_index("ix_api_keys_workspace_id", table_name="api_keys")
        op.drop_table("api_keys")
