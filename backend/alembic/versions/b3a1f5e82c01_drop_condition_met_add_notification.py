"""drop condition_met add notification

Revision ID: b3a1f5e82c01
Revises: da72788361dd
Create Date: 2026-02-02 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3a1f5e82c01"
down_revision: str | None = "da72788361dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("task_executions", sa.Column("notification", sa.Text(), nullable=True))
    op.execute(
        "UPDATE task_executions SET notification = change_summary WHERE condition_met = true"
    )
    op.drop_column("task_executions", "condition_met")


def downgrade() -> None:
    op.add_column(
        "task_executions",
        sa.Column("condition_met", sa.Boolean(), nullable=True, server_default=sa.false()),
    )
    op.execute("UPDATE task_executions SET condition_met = true WHERE notification IS NOT NULL")
    op.drop_column("task_executions", "notification")
