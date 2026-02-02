"""next_run replaces schedule

Revision ID: da72788361dd
Revises: 82cdf3d44858
Create Date: 2026-02-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da72788361dd"
down_revision: str | Sequence[str] | None = "82cdf3d44858"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add next_run column
    op.add_column("tasks", sa.Column("next_run", sa.TIMESTAMP(timezone=True), nullable=True))

    # Backfill: active tasks get now + 24h, completed/paused get NULL
    op.execute(
        """
        UPDATE tasks
        SET next_run = NOW() + INTERVAL '24 hours'
        WHERE state = 'active'
        """
    )

    # Drop schedule from tasks and task_templates (if they exist)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    task_cols = {c["name"] for c in inspector.get_columns("tasks")}
    if "schedule" in task_cols:
        op.drop_column("tasks", "schedule")

    template_cols = {c["name"] for c in inspector.get_columns("task_templates")}
    if "schedule" in template_cols:
        op.drop_column("task_templates", "schedule")


def downgrade() -> None:
    # Re-add schedule columns
    op.add_column(
        "tasks",
        sa.Column("schedule", sa.Text(), server_default="0 */6 * * *", nullable=False),
    )
    op.add_column(
        "task_templates",
        sa.Column("schedule", sa.Text(), server_default="0 */6 * * *", nullable=False),
    )

    # Drop next_run
    op.drop_column("tasks", "next_run")
