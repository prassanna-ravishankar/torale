"""drop_stale_config_column

Revision ID: 82cdf3d44858
Revises: af3fbab7ddc8
Create Date: 2026-02-02 00:10:45.780817

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "82cdf3d44858"
down_revision: Union[str, Sequence[str], None] = "af3fbab7ddc8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop columns removed in v3 that still exist in pre-squash databases."""
    op.drop_column("tasks", "config")
    op.drop_column("tasks", "executor_type")
    op.drop_column("tasks", "extraction_schema")
    op.drop_column("task_templates", "config")


def downgrade() -> None:
    """Re-add dropped columns."""
    op.add_column("tasks", sa.Column("config", sa.JSON(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("executor_type", sa.Text(), server_default="llm_grounded_search", nullable=False),
    )
    op.add_column("tasks", sa.Column("extraction_schema", sa.JSON(), nullable=True))
    op.add_column("task_templates", sa.Column("config", sa.JSON(), nullable=True))
