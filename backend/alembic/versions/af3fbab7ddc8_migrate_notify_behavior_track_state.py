"""migrate_notify_behavior_track_state

Revision ID: af3fbab7ddc8
Revises: 9aec4cc24632
Create Date: 2026-02-01 23:10:53.839749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af3fbab7ddc8'
down_revision: Union[str, Sequence[str], None] = '9aec4cc24632'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate track_state notify_behavior to always."""
    op.execute("""
        UPDATE task_templates
        SET notify_behavior = 'always'
        WHERE notify_behavior = 'track_state'
    """)
    op.execute("""
        UPDATE tasks
        SET notify_behavior = 'always'
        WHERE notify_behavior = 'track_state'
    """)


def downgrade() -> None:
    """Revert track_state migration (no-op since data is lost)."""
    pass
