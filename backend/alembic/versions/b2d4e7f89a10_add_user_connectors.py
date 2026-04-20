"""add user_connectors

Revision ID: b2d4e7f89a10
Revises: a7b8c9d0e1f2
Create Date: 2026-04-20 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b2d4e7f89a10"
down_revision: str = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE user_connectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            toolkit_slug TEXT NOT NULL,
            connected_account_id TEXT,
            status TEXT NOT NULL DEFAULT 'INITIATED'
                CHECK (status IN ('ACTIVE', 'INITIATED', 'EXPIRED', 'FAILED', 'INACTIVE')),
            status_reason TEXT,
            connected_at TIMESTAMP WITH TIME ZONE,
            last_used_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_user_connectors_user_toolkit "
        "ON user_connectors(user_id, toolkit_slug)"
    )
    op.execute("CREATE INDEX idx_user_connectors_user_id ON user_connectors(user_id)")
    op.execute("CREATE INDEX idx_user_connectors_status ON user_connectors(status)")
    op.execute("""
        CREATE TRIGGER update_user_connectors_updated_at
            BEFORE UPDATE ON user_connectors
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_connectors CASCADE")
