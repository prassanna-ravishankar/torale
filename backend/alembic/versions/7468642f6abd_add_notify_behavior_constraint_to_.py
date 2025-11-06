"""add_notify_behavior_constraint_to_templates

Revision ID: 7468642f6abd
Revises: 1ccec0168405
Create Date: 2025-11-06 21:12:04.403972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7468642f6abd'
down_revision: Union[str, Sequence[str], None] = '1ccec0168405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CHECK constraint to task_templates.notify_behavior column."""
    op.create_check_constraint(
        "chk_templates_notify_behavior",
        "task_templates",
        "notify_behavior IN ('once', 'always', 'track_state')",
    )


def downgrade() -> None:
    """Remove CHECK constraint from task_templates.notify_behavior column."""
    op.drop_constraint(
        "chk_templates_notify_behavior",
        "task_templates",
        type_="check",
    )
