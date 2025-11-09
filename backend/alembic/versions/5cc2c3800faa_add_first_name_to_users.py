"""add first_name to users

Revision ID: 5cc2c3800faa
Revises: fc5af45d5080
Create Date: 2025-11-09 19:49:30.069739

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5cc2c3800faa"
down_revision: str | Sequence[str] | None = "fc5af45d5080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add first_name field to users table for email personalization."""
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS first_name TEXT
    """)


def downgrade() -> None:
    """Remove first_name field from users table."""
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS first_name
    """)
