"""add shareable tasks and usernames

Revision ID: a1b2c3d4e5f6
Revises: 961f8ac4183a
Create Date: 2025-12-05 20:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "961f8ac4183a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add shareable tasks and username support."""

    # Add username to users table
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE
    """)

    # Create index on username
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username
        ON users(username)
    """)

    # Add shareable task fields to tasks table
    op.execute("""
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT false,
        ADD COLUMN IF NOT EXISTS slug VARCHAR(255),
        ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS subscriber_count INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS forked_from_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL
    """)

    # Create indexes for tasks
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_is_public
        ON tasks(is_public)
        WHERE is_public = true
    """)

    # Create composite index for username + slug lookups (for vanity URLs)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_user_slug
        ON tasks(user_id, slug)
        WHERE slug IS NOT NULL
    """)

    # Create index on forked_from for analytics
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_forked_from
        ON tasks(forked_from_task_id)
        WHERE forked_from_task_id IS NOT NULL
    """)

    # Create reserved_usernames table (optional but recommended)
    op.execute("""
        CREATE TABLE IF NOT EXISTS reserved_usernames (
            username VARCHAR(50) PRIMARY KEY
        )
    """)

    # Insert reserved usernames
    op.execute("""
        INSERT INTO reserved_usernames (username) VALUES
            ('admin'),
            ('api'),
            ('explore'),
            ('settings'),
            ('support'),
            ('help'),
            ('www'),
            ('app'),
            ('dashboard'),
            ('tasks'),
            ('public'),
            ('auth'),
            ('signin'),
            ('signup'),
            ('login'),
            ('logout'),
            ('register')
        ON CONFLICT (username) DO NOTHING
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop reserved_usernames table
    op.execute("DROP TABLE IF EXISTS reserved_usernames CASCADE")

    # Remove indexes from tasks
    op.execute("DROP INDEX IF EXISTS idx_tasks_forked_from")
    op.execute("DROP INDEX IF EXISTS idx_tasks_user_slug")
    op.execute("DROP INDEX IF EXISTS idx_tasks_is_public")

    # Remove columns from tasks
    op.execute("""
        ALTER TABLE tasks
        DROP COLUMN IF EXISTS forked_from_task_id,
        DROP COLUMN IF EXISTS subscriber_count,
        DROP COLUMN IF EXISTS view_count,
        DROP COLUMN IF EXISTS slug,
        DROP COLUMN IF EXISTS is_public
    """)

    # Remove index from users
    op.execute("DROP INDEX IF EXISTS idx_users_username")

    # Remove column from users
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS username
    """)
