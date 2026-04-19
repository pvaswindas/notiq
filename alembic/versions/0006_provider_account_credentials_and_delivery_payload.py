"""store provider credentials as json and persist delivery payloads

Revision ID: 0006_provider_account_credentials_and_delivery_payload
Revises: 0005_audit_logs
Create Date: 2026-04-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0006_provider_account_credentials_and_delivery_payload"
down_revision: Union[str, None] = "0005_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate provider credentials and delivery payloads to structured JSON.

    This function:
    - Adds `provider_accounts.credentials` as JSONB and backfills existing
      string references into a structured payload.
    - Removes the legacy `credentials_ref` column.
    - Adds `delivery_jobs.event_payload` as JSONB and backfills it from the
      stored delivery message for previously created jobs.

    Returns:
        None

    Important:
    - The migration preserves retryability by storing delivery context in the
      durable job record.
    - Existing provider-account rows are normalized so new code can depend on
      `credentials` being present.
    """

    op.add_column(
        "provider_accounts",
        sa.Column(
            "credentials",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.execute(
        """
        UPDATE provider_accounts
        SET credentials = CASE
            WHEN credentials_ref IS NULL OR btrim(credentials_ref) = '' THEN '{}'::jsonb
            ELSE jsonb_build_object('value', credentials_ref)
        END
        """
    )
    op.alter_column("provider_accounts", "credentials", nullable=False, server_default=None)
    op.drop_column("provider_accounts", "credentials_ref")

    op.add_column(
        "delivery_jobs",
        sa.Column(
            "event_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.execute(
        """
        UPDATE delivery_jobs
        SET event_payload = jsonb_build_object('message', message)
        WHERE event_payload IS NULL OR event_payload = '{}'::jsonb
        """
    )
    op.alter_column("delivery_jobs", "event_payload", nullable=False, server_default=None)


def downgrade() -> None:
    """Restore the pre-JSON credential layout and remove event payload storage.

    This function:
    - Recreates `credentials_ref` from structured provider credentials.
    - Drops `provider_accounts.credentials`.
    - Removes `delivery_jobs.event_payload`.

    Returns:
        None

    Important:
    - Downgrade keeps only the credential value that can be projected back into
      the legacy string column, so structured provider data may be reduced.
    """

    op.add_column("provider_accounts", sa.Column("credentials_ref", sa.String(length=255), nullable=True))
    op.execute(
        """
        UPDATE provider_accounts
        SET credentials_ref = COALESCE(credentials->>'bot_token', credentials->>'value', '')
        """
    )
    op.alter_column("provider_accounts", "credentials_ref", nullable=False)
    op.drop_column("provider_accounts", "credentials")

    op.drop_column("delivery_jobs", "event_payload")
