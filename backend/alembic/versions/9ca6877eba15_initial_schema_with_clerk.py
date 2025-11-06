"""initial_schema_with_clerk

This is the consolidated initial migration that includes:
- Clerk authentication (replaces FastAPI-Users)
- Grounded search fields
- API keys table

Previous migrations (c9da50682126, 30d7793fb7d2, 7e4bc3017b35) have been consolidated here.

Revision ID: 9ca6877eba15
Revises:
Create Date: 2025-11-04 09:50:25.913930

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ca6877eba15"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Drop any existing tables from previous installations
    op.execute("DROP TABLE IF EXISTS task_executions CASCADE")
    op.execute("DROP TABLE IF EXISTS tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")

    # Recreate users table with Clerk fields
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            clerk_user_id TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_clerk_user_id
        ON users(clerk_user_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    """)

    # Recreate tasks table (from initial migration)
    op.execute("""
        CREATE TABLE tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            schedule TEXT NOT NULL,
            executor_type TEXT NOT NULL DEFAULT 'llm_grounded_search',
            config JSONB NOT NULL,
            is_active BOOLEAN DEFAULT true,

            -- Grounded search fields
            search_query TEXT,
            condition_description TEXT,
            notify_behavior TEXT DEFAULT 'once',
            condition_met BOOLEAN DEFAULT false,
            last_known_state JSONB,
            last_notified_at TIMESTAMP WITH TIME ZONE,

            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Add constraints
    op.execute("""
        ALTER TABLE tasks
        ADD CONSTRAINT check_notify_behavior
        CHECK (notify_behavior IN ('once', 'always', 'track_state'))
    """)

    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_user_id
        ON tasks(user_id)
    """)

    # Recreate task_executions table
    op.execute("""
        CREATE TABLE task_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            result JSONB,
            error_message TEXT,

            -- Grounded search fields
            condition_met BOOLEAN,
            change_summary TEXT,
            grounding_sources JSONB,

            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_task_executions_task_id
        ON task_executions(task_id)
    """)

    # Create API keys table for CLI authentication
    op.execute("""
        CREATE TABLE api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            key_prefix TEXT NOT NULL,
            key_hash TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)

    # Create indexes on api_keys
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_keys_user_id
        ON api_keys(user_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash
        ON api_keys(key_hash) WHERE is_active = true
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop all tables
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    op.execute("DROP TABLE IF EXISTS task_executions CASCADE")
    op.execute("DROP TABLE IF EXISTS tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
