"""auto verify clerk emails

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-08 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Auto-verify Clerk emails for all existing users.

    Adds each user's Clerk email (from users.email field) to their
    verified_notification_emails array so they can immediately use
    notifications without manual verification.
    """
    op.execute("""
        UPDATE users
        SET verified_notification_emails =
            array_append(
                COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                email
            )
        WHERE email IS NOT NULL
          AND NOT (email = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[])))
    """)


def downgrade() -> None:
    """
    Remove Clerk emails from verified_notification_emails.

    Note: This only removes emails that match the current Clerk email.
    Manually verified custom emails are preserved.
    """
    op.execute("""
        UPDATE users
        SET verified_notification_emails =
            array_remove(
                COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                email
            )
        WHERE email IS NOT NULL
          AND email = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[]))
    """)
