"""add grounded search fields

Revision ID: 30d7793fb7d2
Revises: c9da50682126
Create Date: 2025-11-04 00:10:54.796498

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "30d7793fb7d2"
down_revision: str | Sequence[str] | None = "c9da50682126"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add grounded search fields to tasks table
    op.execute("""
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS search_query TEXT,
        ADD COLUMN IF NOT EXISTS condition_description TEXT,
        ADD COLUMN IF NOT EXISTS notify_behavior TEXT DEFAULT 'once',
        ADD COLUMN IF NOT EXISTS condition_met BOOLEAN DEFAULT false,
        ADD COLUMN IF NOT EXISTS last_known_state JSONB,
        ADD COLUMN IF NOT EXISTS last_notified_at TIMESTAMP WITH TIME ZONE
    """)

    # Add check constraint for notify_behavior
    op.execute("""
        ALTER TABLE tasks
        ADD CONSTRAINT check_notify_behavior
        CHECK (notify_behavior IN ('once', 'always', 'track_state'))
    """)

    # Add grounded search fields to task_executions table
    op.execute("""
        ALTER TABLE task_executions
        ADD COLUMN IF NOT EXISTS condition_met BOOLEAN,
        ADD COLUMN IF NOT EXISTS change_summary TEXT,
        ADD COLUMN IF NOT EXISTS grounding_sources JSONB
    """)

    # Update default executor_type (optional - keeps backward compatibility)
    # Existing tasks will keep their executor_type
    # New tasks will default to llm_grounded_search when created


def downgrade() -> None:
    """Downgrade schema."""
    # Remove fields from task_executions
    op.execute("""
        ALTER TABLE task_executions
        DROP COLUMN IF EXISTS condition_met,
        DROP COLUMN IF EXISTS change_summary,
        DROP COLUMN IF EXISTS grounding_sources
    """)

    # Remove fields from tasks
    op.execute("""
        ALTER TABLE tasks
        DROP CONSTRAINT IF EXISTS check_notify_behavior,
        DROP COLUMN IF EXISTS search_query,
        DROP COLUMN IF EXISTS condition_description,
        DROP COLUMN IF EXISTS notify_behavior,
        DROP COLUMN IF EXISTS condition_met,
        DROP COLUMN IF EXISTS last_known_state,
        DROP COLUMN IF EXISTS last_notified_at
    """)
