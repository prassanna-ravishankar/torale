"""add tasks.attached_connector_slugs

Revision ID: c5e8f9d23b41
Revises: b2d4e7f89a10
Create Date: 2026-04-20 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c5e8f9d23b41"
down_revision: str = "b2d4e7f89a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tasks "
        "ADD COLUMN attached_connector_slugs TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[]"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS attached_connector_slugs")
