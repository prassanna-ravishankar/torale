"""add state_changed_at to tasks

Revision ID: 961f8ac4183a
Revises: 79d49a430c3f
Create Date: 2025-12-04 07:09:49.819670

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "961f8ac4183a"
down_revision: str | Sequence[str] | None = "79d49a430c3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add state_changed_at column to track when task state last changed."""
    # Add state_changed_at column with default NOW() for new rows
    op.add_column(
        "tasks",
        sa.Column(
            "state_changed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Backfill existing rows: set state_changed_at to updated_at (if exists) or created_at
    # This provides the best approximation for when state last changed
    op.execute("""
        UPDATE tasks
        SET state_changed_at = COALESCE(updated_at, created_at)
    """)


def downgrade() -> None:
    """Remove state_changed_at column."""
    op.drop_column("tasks", "state_changed_at")
