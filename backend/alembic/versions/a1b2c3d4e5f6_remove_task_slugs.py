"""remove task slugs

Revision ID: a1b2c3d4e5f6
Revises: f3a8c2e91d47
Create Date: 2026-03-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f3a8c2e91d47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("idx_tasks_user_slug", table_name="tasks")
    op.drop_column("tasks", "slug")


def downgrade() -> None:
    op.add_column("tasks", sa.Column("slug", sa.VARCHAR(length=100), nullable=True))
    op.create_index("idx_tasks_user_slug", "tasks", ["user_id", "slug"], unique=True)
