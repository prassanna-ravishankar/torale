"""add_api_keys_table

Revision ID: 7e4bc3017b35
Revises: 30d7793fb7d2
Create Date: 2025-11-04 09:50:04.057944

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e4bc3017b35"
down_revision: str | Sequence[str] | None = "30d7793fb7d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create API keys table for CLI authentication
    op.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            key_prefix TEXT NOT NULL,
            key_hash TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)

    # Create index on user_id for faster lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_keys_user_id
        ON api_keys(user_id)
    """)

    # Create index on key_hash for auth lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash
        ON api_keys(key_hash) WHERE is_active = true
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE")
