"""initial_schema

Revision ID: c9da50682126
Revises:
Create Date: 2025-11-03 22:31:31.567233

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9da50682126"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create users table (for FastAPI-Users)
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(320) UNIQUE NOT NULL,
            hashed_password VARCHAR(1024) NOT NULL,
            is_active BOOLEAN DEFAULT true NOT NULL,
            is_superuser BOOLEAN DEFAULT false NOT NULL,
            is_verified BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create tasks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
            name TEXT NOT NULL,
            schedule TEXT NOT NULL,
            executor_type TEXT NOT NULL DEFAULT 'llm_text',
            config JSONB NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create task_executions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            result JSONB,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'success', 'failed'))
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_users_email ON users(email)")
    op.execute("CREATE INDEX idx_tasks_user_id ON tasks(user_id)")
    op.execute("CREATE INDEX idx_tasks_is_active ON tasks(is_active)")
    op.execute("CREATE INDEX idx_task_executions_task_id ON task_executions(task_id)")
    op.execute("CREATE INDEX idx_task_executions_status ON task_executions(status)")

    # Create update trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER update_tasks_updated_at
            BEFORE UPDATE ON tasks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    op.execute("DROP TABLE IF EXISTS task_executions CASCADE")
    op.execute("DROP TABLE IF EXISTS tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
