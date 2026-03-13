"""drop_notify_behavior

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-03-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop notify_behavior column from tasks and task_templates."""
    # tasks: drop CHECK constraint first, then column
    op.drop_constraint("check_notify_behavior", "tasks", type_="check")
    op.drop_column("tasks", "notify_behavior")

    # task_templates: drop CHECK constraint first, then column
    op.drop_constraint("chk_templates_notify_behavior", "task_templates", type_="check")
    op.drop_column("task_templates", "notify_behavior")


def downgrade() -> None:
    """Re-add notify_behavior column to tasks and task_templates."""
    op.add_column(
        "tasks",
        sa.Column("notify_behavior", sa.Text(), server_default="once"),
    )
    op.create_check_constraint(
        "check_notify_behavior",
        "tasks",
        "notify_behavior IN ('once', 'always')",
    )

    op.add_column(
        "task_templates",
        sa.Column("notify_behavior", sa.VARCHAR(50), nullable=False, server_default="always"),
    )
    op.create_check_constraint(
        "chk_templates_notify_behavior",
        "task_templates",
        "notify_behavior IN ('once', 'always')",
    )
