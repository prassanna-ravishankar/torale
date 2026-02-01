"""drop pipeline columns

Revision ID: e95666a4cd0e
Revises: 189283387c51
Create Date: 2025-02-01

Drop obsolete pipeline-era columns from tasks table:
- extraction_schema (JSONB, never populated by agent)
- condition_met (BOOLEAN, deprecated — use last_execution.condition_met)
- last_notified_at (TIMESTAMP, deprecated — not used by agent flow)
- executor_type (TEXT, always "llm_grounded_search")
- config (JSONB, always {"search_provider":"google"})
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e95666a4cd0e"
down_revision = "189283387c51"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("tasks", "extraction_schema")
    op.drop_column("tasks", "condition_met")
    op.drop_column("tasks", "last_notified_at")
    op.drop_column("tasks", "executor_type")
    op.drop_column("tasks", "config")


def downgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "config",
            postgresql.JSONB(),
            server_default=sa.text('\'{"search_provider": "google"}\'::jsonb'),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "executor_type",
            sa.Text(),
            server_default="llm_grounded_search",
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column("last_notified_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("condition_met", sa.Boolean(), server_default="false", nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("extraction_schema", postgresql.JSONB(), nullable=True),
    )
