"""add notifications to tasks

Revision ID: 5ba730c9c123
Revises: 3dcde9bea1b3
Create Date: 2025-11-07 22:40:09.036578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ba730c9c123'
down_revision: Union[str, Sequence[str], None] = '3dcde9bea1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add notifications column to tasks table
    op.add_column(
        'tasks',
        sa.Column('notifications', sa.JSON(), nullable=False, server_default='[]')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove notifications column
    op.drop_column('tasks', 'notifications')
