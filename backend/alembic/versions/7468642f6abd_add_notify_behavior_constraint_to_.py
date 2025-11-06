"""add_notify_behavior_constraint_to_templates

Revision ID: 7468642f6abd
Revises: 1ccec0168405
Create Date: 2025-11-06 21:12:04.403972

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7468642f6abd"
down_revision: str | Sequence[str] | None = "1ccec0168405"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add CHECK constraint to task_templates.notify_behavior column if it doesn't exist."""
    # Check if constraint already exists (for fresh installs that got it from 0c195cb8b608)
    connection = op.get_bind()
    result = connection.execute(
        sa.text("""
            SELECT COUNT(*)
            FROM pg_constraint
            WHERE conname = 'chk_templates_notify_behavior'
        """)
    )
    constraint_exists = result.scalar() > 0

    if not constraint_exists:
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
