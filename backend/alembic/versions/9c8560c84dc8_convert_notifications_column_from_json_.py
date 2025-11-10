"""convert notifications column from json to jsonb

Revision ID: 9c8560c84dc8
Revises: 5ba730c9c123
Create Date: 2025-11-10 23:32:37.787332

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c8560c84dc8"
down_revision: str | Sequence[str] | None = "5ba730c9c123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - convert notifications column from JSON to JSONB."""
    # Alter the column type from JSON to JSONB
    # USING clause converts existing JSON data to JSONB format
    op.execute("""
        ALTER TABLE tasks
        ALTER COLUMN notifications
        TYPE jsonb
        USING notifications::jsonb
    """)


def downgrade() -> None:
    """Downgrade schema - convert notifications column from JSONB to JSON."""
    # Alter the column type from JSONB back to JSON
    op.execute("""
        ALTER TABLE tasks
        ALTER COLUMN notifications
        TYPE json
        USING notifications::json
    """)
