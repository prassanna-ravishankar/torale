"""add notifications to tasks

Revision ID: 5ba730c9c123
Revises: 5cc2c3800faa
Create Date: 2025-11-07 22:40:09.036578

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ba730c9c123"
down_revision: str | Sequence[str] | None = "5cc2c3800faa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add notifications column to tasks table (using JSONB for PostgreSQL performance)
    op.add_column(
        "tasks",
        sa.Column("notifications", postgresql.JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove notifications column
    op.drop_column("tasks", "notifications")
