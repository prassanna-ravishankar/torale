"""add last_execution_id to tasks

Revision ID: c36fe95dcb98
Revises: f3004543fd24
Create Date: 2025-11-30 12:08:42.305879

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c36fe95dcb98"
down_revision: str | Sequence[str] | None = "f3004543fd24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add last_execution_id for efficient lookup of latest execution
    op.add_column("tasks", sa.Column("last_execution_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_last_execution",
        "tasks",
        "task_executions",
        ["last_execution_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill last_execution_id from latest execution per task
    # This finds the most recent execution (by started_at) for each task
    op.execute(
        """
        UPDATE tasks t
        SET last_execution_id = (
            SELECT e.id
            FROM task_executions e
            WHERE e.task_id = t.id
            ORDER BY e.started_at DESC
            LIMIT 1
        )
    """
    )

    # NOTE: We do NOT drop condition_met and last_notified_at columns yet
    # This allows gradual migration - frontend can use old fields during transition
    # A follow-up migration will drop these columns after confirming everything works


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint("fk_tasks_last_execution", "tasks", type_="foreignkey")

    # Drop last_execution_id column
    op.drop_column("tasks", "last_execution_id")
