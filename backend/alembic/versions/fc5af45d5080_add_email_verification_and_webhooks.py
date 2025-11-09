"""add email verification and webhooks

Revision ID: fc5af45d5080
Revises: 3dcde9bea1b3
Create Date: 2025-11-09 19:18:32.726256

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fc5af45d5080"
down_revision: str | Sequence[str] | None = "3dcde9bea1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add email verification, webhooks, and notification tracking."""

    # Add email verification and webhook fields to users table
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS verified_notification_emails TEXT[] DEFAULT ARRAY[]::TEXT[],
        ADD COLUMN IF NOT EXISTS webhook_url TEXT,
        ADD COLUMN IF NOT EXISTS webhook_secret TEXT,
        ADD COLUMN IF NOT EXISTS webhook_enabled BOOLEAN DEFAULT false
    """)

    # Add notification channel and webhook fields to tasks table
    op.execute("""
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS notification_channels TEXT[] DEFAULT ARRAY['email']::TEXT[],
        ADD COLUMN IF NOT EXISTS notification_email TEXT,
        ADD COLUMN IF NOT EXISTS webhook_url TEXT,
        ADD COLUMN IF NOT EXISTS webhook_secret TEXT,
        ADD CONSTRAINT check_notification_channels
            CHECK (notification_channels <@ ARRAY['email', 'webhook']::TEXT[])
    """)

    # Create email_verifications table
    op.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
            email TEXT NOT NULL,
            verification_code TEXT NOT NULL,
            verified BOOLEAN DEFAULT false,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            verified_at TIMESTAMP WITH TIME ZONE,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create indexes for email_verifications
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_email_verifications_code
        ON email_verifications(verification_code)
        WHERE verified = false
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_email_verification
        ON email_verifications(user_id, email)
        WHERE verified = false
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_email_verifications_user_created
        ON email_verifications(user_id, created_at)
    """)

    # Create notification_sends table for spam tracking
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_sends (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            recipient_email TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create indexes for notification_sends
    op.execute("""
        CREATE INDEX idx_notification_sends_user_time
        ON notification_sends(user_id, sent_at)
    """)
    op.execute("""
        CREATE INDEX idx_notification_sends_email_time
        ON notification_sends(recipient_email, sent_at)
    """)

    # Create webhook_deliveries table
    op.execute("""
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
            execution_id UUID REFERENCES task_executions(id) ON DELETE CASCADE,
            webhook_url TEXT NOT NULL,
            payload JSONB NOT NULL,
            signature TEXT NOT NULL,
            http_status INTEGER,
            response_body TEXT,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            delivered_at TIMESTAMP WITH TIME ZONE,
            failed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            next_retry_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create indexes for webhook_deliveries
    op.execute("""
        CREATE INDEX idx_webhook_deliveries_task_id
        ON webhook_deliveries(task_id)
    """)
    op.execute("""
        CREATE INDEX idx_webhook_deliveries_next_retry
        ON webhook_deliveries(next_retry_at)
        WHERE delivered_at IS NULL AND failed_at IS NULL
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables
    op.execute("DROP TABLE IF EXISTS webhook_deliveries CASCADE")
    op.execute("DROP TABLE IF EXISTS notification_sends CASCADE")
    op.execute("DROP TABLE IF EXISTS email_verifications CASCADE")

    # Remove constraint from tasks
    op.execute("ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_notification_channels")

    # Remove columns from tasks
    op.execute("""
        ALTER TABLE tasks
        DROP COLUMN IF EXISTS webhook_secret,
        DROP COLUMN IF EXISTS webhook_url,
        DROP COLUMN IF EXISTS notification_email,
        DROP COLUMN IF EXISTS notification_channels
    """)

    # Remove columns from users
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS webhook_enabled,
        DROP COLUMN IF EXISTS webhook_secret,
        DROP COLUMN IF EXISTS webhook_url,
        DROP COLUMN IF EXISTS verified_notification_emails
    """)
