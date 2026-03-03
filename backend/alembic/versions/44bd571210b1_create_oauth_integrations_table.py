"""create oauth_integrations table

Revision ID: 44bd571210b1
Revises: 42235af69f7d
Create Date: 2026-02-12 23:31:15.350862

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "44bd571210b1"
down_revision: str | Sequence[str] | None = "42235af69f7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create oauth_integrations table for Slack/Discord OAuth."""
    op.execute("""
        CREATE TABLE oauth_integrations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider TEXT NOT NULL CHECK (provider IN ('slack', 'discord')),

            -- OAuth tokens (encrypt in production)
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expires_at TIMESTAMP WITH TIME ZONE,

            -- Provider-specific metadata
            workspace_id TEXT,
            workspace_name TEXT,
            channel_id TEXT,
            channel_name TEXT,

            -- Metadata
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_used_at TIMESTAMP WITH TIME ZONE,

            UNIQUE(user_id, provider)
        )
    """)
    op.execute("CREATE INDEX idx_oauth_integrations_user_id ON oauth_integrations(user_id)")
    op.execute("CREATE INDEX idx_oauth_integrations_provider ON oauth_integrations(provider)")


def downgrade() -> None:
    """Drop oauth_integrations table."""
    op.execute("DROP TABLE IF EXISTS oauth_integrations")
