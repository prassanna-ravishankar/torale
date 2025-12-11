"""add_unique_constraint_user_task_name

Revision ID: 64e7f3797d90
Revises: a1b2c3d4e5f6
Create Date: 2025-12-11 13:23:19.598536

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "64e7f3797d90"
down_revision: str | Sequence[str] | None = "5c6d7e8f9a0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add UNIQUE constraint on (user_id, name) to prevent duplicate task names per user."""
    # Add unique constraint to ensure no duplicate task names per user
    # This enables robust handling of race conditions in fork name generation
    op.create_unique_constraint("uq_tasks_user_id_name", "tasks", ["user_id", "name"])


def downgrade() -> None:
    """Remove UNIQUE constraint on (user_id, name)."""
    op.drop_constraint("uq_tasks_user_id_name", "tasks", type_="unique")
