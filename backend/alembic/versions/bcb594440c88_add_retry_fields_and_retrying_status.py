"""add_retry_fields_and_retrying_status

Revision ID: bcb594440c88
Revises: c4e2a9b71f03
Create Date: 2026-02-06 21:45:57.957514

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bcb594440c88"
down_revision: str | Sequence[str] | None = "c4e2a9b71f03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # The status column is TEXT, not an enum type, so no enum alteration needed
    # The 'retrying' status can be used directly as a text value

    # Add retry tracking columns to task_executions
    op.add_column(
        "task_executions",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("task_executions", sa.Column("error_category", sa.Text(), nullable=True))
    op.add_column("task_executions", sa.Column("internal_error", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove retry tracking columns
    op.drop_column("task_executions", "internal_error")
    op.drop_column("task_executions", "error_category")
    op.drop_column("task_executions", "retry_count")

    # Note: Cannot remove enum value in PostgreSQL without recreating the type
    # This would require more complex migration with data preservation
