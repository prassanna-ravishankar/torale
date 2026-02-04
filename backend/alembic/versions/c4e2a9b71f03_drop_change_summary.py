"""drop change_summary from task_executions

Revision ID: c4e2a9b71f03
Revises: b3a1f5e82c01
Create Date: 2026-02-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4e2a9b71f03"
down_revision: str | None = "b3a1f5e82c01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("task_executions", "change_summary")


def downgrade() -> None:
    op.add_column("task_executions", sa.Column("change_summary", sa.Text(), nullable=True))
