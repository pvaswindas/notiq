"""add admin rbac tables

Revision ID: 0004_admin_rbac
Revises: 0003_api_keys_auth
Create Date: 2026-04-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_admin_rbac"
down_revision: Union[str, None] = "0003_api_keys_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "admins"):
        op.create_table(
            "admins",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index(inspector, "admins", "ux_admins_email"):
        op.create_index("ux_admins_email", "admins", ["email"], unique=True)

    if not _has_table(inspector, "roles"):
        op.create_table(
            "roles",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index(inspector, "roles", "ux_roles_name"):
        op.create_index("ux_roles_name", "roles", ["name"], unique=True)

    if not _has_table(inspector, "permissions"):
        op.create_table(
            "permissions",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index(inspector, "permissions", "ux_permissions_name"):
        op.create_index("ux_permissions_name", "permissions", ["name"], unique=True)

    if not _has_table(inspector, "role_permissions"):
        op.create_table(
            "role_permissions",
            sa.Column("role_id", sa.String(length=64), nullable=False),
            sa.Column("permission_id", sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("role_id", "permission_id"),
        )

    if not _has_index(inspector, "role_permissions", "ix_role_permissions_permission_id"):
        op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    if not _has_table(inspector, "admin_roles"):
        op.create_table(
            "admin_roles",
            sa.Column("admin_id", sa.String(length=64), nullable=False),
            sa.Column("role_id", sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("admin_id", "role_id"),
        )

    if not _has_index(inspector, "admin_roles", "ix_admin_roles_role_id"):
        op.create_index("ix_admin_roles_role_id", "admin_roles", ["role_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "admin_roles"):
        if _has_index(inspector, "admin_roles", "ix_admin_roles_role_id"):
            op.drop_index("ix_admin_roles_role_id", table_name="admin_roles")
        op.drop_table("admin_roles")

    if _has_table(inspector, "role_permissions"):
        if _has_index(inspector, "role_permissions", "ix_role_permissions_permission_id"):
            op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
        op.drop_table("role_permissions")

    if _has_table(inspector, "permissions"):
        if _has_index(inspector, "permissions", "ux_permissions_name"):
            op.drop_index("ux_permissions_name", table_name="permissions")
        op.drop_table("permissions")

    if _has_table(inspector, "roles"):
        if _has_index(inspector, "roles", "ux_roles_name"):
            op.drop_index("ux_roles_name", table_name="roles")
        op.drop_table("roles")

    if _has_table(inspector, "admins"):
        if _has_index(inspector, "admins", "ux_admins_email"):
            op.drop_index("ux_admins_email", table_name="admins")
        op.drop_table("admins")
