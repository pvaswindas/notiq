"""add dead letter jobs table for terminal delivery failures

Revision ID: 0007_dead_letter_jobs
Revises: 0006_provider_account_credentials_and_delivery_payload
Create Date: 2026-04-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0007_dead_letter_jobs"
down_revision: Union[str, None] = "0006_provider_account_credentials_and_delivery_payload"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dead_letter_jobs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column(
            "original_job_id",
            sa.String(length=64),
            sa.ForeignKey("delivery_jobs.job_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=64),
            sa.ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            sa.String(length=64),
            sa.ForeignKey("channels.channel_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("failure_reason", sa.Text(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("original_job_id", name="uq_dead_letter_jobs_original_job_id"),
    )
    op.create_index("ix_dead_letter_jobs_workspace_created", "dead_letter_jobs", ["workspace_id", "created_at"])
    op.create_index("ix_dead_letter_jobs_workspace_channel", "dead_letter_jobs", ["workspace_id", "channel_id"])
    op.alter_column("dead_letter_jobs", "payload", server_default=None)
    op.alter_column("dead_letter_jobs", "failure_count", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_dead_letter_jobs_workspace_channel", table_name="dead_letter_jobs")
    op.drop_index("ix_dead_letter_jobs_workspace_created", table_name="dead_letter_jobs")
    op.drop_table("dead_letter_jobs")

