"""update model to gemini 2.5 flash

Revision ID: 3dcde9bea1b3
Revises: 40f825e86987
Create Date: 2025-11-07 22:03:12.949896

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3dcde9bea1b3"
down_revision: str | Sequence[str] | None = "40f825e86987"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update existing task templates and tasks to use gemini-2.5-flash."""
    # Update task_templates config
    # Cast to jsonb for compatibility with both json and jsonb columns
    op.execute("""
        UPDATE task_templates
        SET config = jsonb_set(config::jsonb, '{model}', '"gemini-2.5-flash"')::json
        WHERE config->>'model' = 'gemini-2.0-flash-exp'
    """)

    # Update tasks config
    op.execute("""
        UPDATE tasks
        SET config = jsonb_set(config::jsonb, '{model}', '"gemini-2.5-flash"')::json
        WHERE config->>'model' = 'gemini-2.0-flash-exp'
    """)


def downgrade() -> None:
    """Revert to gemini-2.0-flash-exp."""
    # Revert task_templates config
    op.execute("""
        UPDATE task_templates
        SET config = jsonb_set(config::jsonb, '{model}', '"gemini-2.0-flash-exp"')::json
        WHERE config->>'model' = 'gemini-2.5-flash'
    """)

    # Revert tasks config
    op.execute("""
        UPDATE tasks
        SET config = jsonb_set(config::jsonb, '{model}', '"gemini-2.0-flash-exp"')::json
        WHERE config->>'model' = 'gemini-2.5-flash'
    """)
