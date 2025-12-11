"""add_view_count_index

Revision ID: e8f9a0b1c2d3
Revises: 64e7f3797d90
Create Date: 2025-12-11 14:15:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8f9a0b1c2d3"
down_revision: str | Sequence[str] | None = "64e7f3797d90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add partial index on view_count for public tasks to optimize popular sorting."""
    # Partial index only on public tasks for efficient sorting by view_count
    # This prevents indexing private tasks which don't appear in public listings
    op.create_index(
        "idx_tasks_public_view_count",
        "tasks",
        ["view_count"],
        unique=False,
        postgresql_where="is_public = true",
    )


def downgrade() -> None:
    """Remove view_count index."""
    op.drop_index("idx_tasks_public_view_count", table_name="tasks")
