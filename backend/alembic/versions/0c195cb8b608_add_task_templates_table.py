"""add_task_templates_table

Revision ID: 0c195cb8b608
Revises: 9ca6877eba15
Create Date: 2025-11-04 23:53:23.980378

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c195cb8b608"
down_revision: str | Sequence[str] | None = "9ca6877eba15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "task_templates",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=False),
        sa.Column("condition_description", sa.Text(), nullable=False),
        sa.Column("schedule", sa.String(length=100), nullable=False),
        sa.Column("notify_behavior", sa.String(length=50), nullable=False),
        sa.Column(
            "config",
            sa.JSON(),
            server_default=sa.text('\'{"model": "gemini-2.0-flash-exp"}\''),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "notify_behavior IN ('once', 'always', 'track_state')",
            name="chk_templates_notify_behavior",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_templates_category", "task_templates", ["category"])
    op.create_index("idx_templates_active", "task_templates", ["is_active"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_templates_active", table_name="task_templates")
    op.drop_index("idx_templates_category", table_name="task_templates")
    op.drop_table("task_templates")
