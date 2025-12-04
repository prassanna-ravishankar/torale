"""add_task_state_column

Revision ID: 79d49a430c3f
Revises: c36fe95dcb98
Create Date: 2025-12-02 23:02:11.482754

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "79d49a430c3f"
down_revision: str | Sequence[str] | None = "c36fe95dcb98"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add state column to tasks table and migrate from is_active."""
    # Add state column with default 'active'
    op.add_column("tasks", sa.Column("state", sa.String(), nullable=False, server_default="active"))

    # Add check constraint for valid states
    op.create_check_constraint(
        "tasks_state_check", "tasks", "state IN ('active', 'paused', 'completed')"
    )

    # Migrate existing data: is_active -> state
    op.execute("""
        UPDATE tasks
        SET state = CASE
            WHEN is_active THEN 'active'
            ELSE 'paused'
        END
    """)

    # Drop is_active column (breaking change)
    op.drop_column("tasks", "is_active")

    # Add indexes for common queries
    op.create_index("idx_tasks_state", "tasks", ["state"])
    op.create_index("idx_tasks_user_state", "tasks", ["user_id", "state"])


def downgrade() -> None:
    """Rollback state column changes and restore is_active."""
    # Re-add is_active column
    op.add_column(
        "tasks", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true")
    )

    # Migrate data back: state -> is_active
    op.execute("UPDATE tasks SET is_active = (state = 'active')")

    # Drop indexes
    op.drop_index("idx_tasks_user_state", "tasks")
    op.drop_index("idx_tasks_state", "tasks")

    # Drop check constraint
    op.drop_constraint("tasks_state_check", "tasks")

    # Drop state column
    op.drop_column("tasks", "state")
