"""add waitlist table

Revision ID: 40f825e86987
Revises: 7468642f6abd
Create Date: 2025-11-07 15:13:58.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "40f825e86987"
down_revision: str | Sequence[str] | None = "7468642f6abd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create waitlist table for managing user signups when at capacity."""
    op.execute("""
        CREATE TABLE waitlist (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'invited', 'converted')),
            invited_at TIMESTAMP WITH TIME ZONE,
            notes TEXT
        )
    """)

    # Create index on status for efficient filtering
    op.create_index("idx_waitlist_status", "waitlist", ["status"])
    op.create_index("idx_waitlist_created_at", "waitlist", ["created_at"])


def downgrade() -> None:
    """Drop waitlist table."""
    op.drop_index("idx_waitlist_created_at", "waitlist")
    op.drop_index("idx_waitlist_status", "waitlist")
    op.drop_table("waitlist")
