"""add_has_seen_welcome

Revision ID: f3a8c2e91d47
Revises: 82cdf3d44858
Create Date: 2026-02-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a8c2e91d47"
down_revision: str | Sequence[str] | None = "82cdf3d44858"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("has_seen_welcome", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("users", "has_seen_welcome")
