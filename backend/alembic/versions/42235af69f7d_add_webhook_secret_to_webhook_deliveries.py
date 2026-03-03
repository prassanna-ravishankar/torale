"""add webhook_secret to webhook_deliveries

Revision ID: 42235af69f7d
Revises: bcb594440c88
Create Date: 2026-02-12 23:29:52.681785

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "42235af69f7d"
down_revision: str | Sequence[str] | None = "bcb594440c88"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add webhook_secret column for retry signature regeneration."""
    op.add_column("webhook_deliveries", sa.Column("webhook_secret", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove webhook_secret column."""
    op.drop_column("webhook_deliveries", "webhook_secret")
