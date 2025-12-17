"""add extraction_schema to tasks

Revision ID: 189283387c51
Revises: e8f9a0b1c2d3
Create Date: 2025-12-17 09:40:06.854921

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "189283387c51"
down_revision: Union[str, Sequence[str], None] = "e8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("extraction_schema", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "extraction_schema")
