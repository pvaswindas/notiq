"""add audit logs table with immutability guard

Revision ID: 0005_audit_logs
Revises: 0004_admin_rbac
Create Date: 2026-04-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_audit_logs"
down_revision: Union[str, None] = "0004_admin_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("actor_id", sa.String(length=64), nullable=True),
            sa.Column("action", sa.String(length=128), nullable=False),
            sa.Column("resource", sa.String(length=128), nullable=False),
            sa.Column("resource_id", sa.String(length=128), nullable=False),
            sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index(inspector, "audit_logs", "ix_audit_logs_created_at"):
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    if not _has_index(inspector, "audit_logs", "ix_audit_logs_actor_created_at"):
        op.create_index("ix_audit_logs_actor_created_at", "audit_logs", ["actor_id", "created_at"])

    if not _has_index(inspector, "audit_logs", "ix_audit_logs_resource_action_created_at"):
        op.create_index(
            "ix_audit_logs_resource_action_created_at",
            "audit_logs",
            ["resource", "action", "created_at"],
        )

    if not _has_index(inspector, "audit_logs", "ix_audit_logs_resource_id_created_at"):
        op.create_index(
            "ix_audit_logs_resource_id_created_at",
            "audit_logs",
            ["resource", "resource_id", "created_at"],
        )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_logs_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only and immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'trg_prevent_audit_logs_update'
            ) THEN
                CREATE TRIGGER trg_prevent_audit_logs_update
                BEFORE UPDATE ON audit_logs
                FOR EACH ROW
                EXECUTE FUNCTION prevent_audit_logs_mutation();
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'trg_prevent_audit_logs_delete'
            ) THEN
                CREATE TRIGGER trg_prevent_audit_logs_delete
                BEFORE DELETE ON audit_logs
                FOR EACH ROW
                EXECUTE FUNCTION prevent_audit_logs_mutation();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_logs_update ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_logs_delete ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_logs_mutation")

    if _has_table(inspector, "audit_logs"):
        if _has_index(inspector, "audit_logs", "ix_audit_logs_resource_id_created_at"):
            op.drop_index("ix_audit_logs_resource_id_created_at", table_name="audit_logs")

        if _has_index(inspector, "audit_logs", "ix_audit_logs_resource_action_created_at"):
            op.drop_index("ix_audit_logs_resource_action_created_at", table_name="audit_logs")

        if _has_index(inspector, "audit_logs", "ix_audit_logs_actor_created_at"):
            op.drop_index("ix_audit_logs_actor_created_at", table_name="audit_logs")

        if _has_index(inspector, "audit_logs", "ix_audit_logs_created_at"):
            op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")

        op.drop_table("audit_logs")
