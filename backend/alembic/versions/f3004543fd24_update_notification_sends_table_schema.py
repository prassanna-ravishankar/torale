"""update notification_sends table schema

Revision ID: f3004543fd24
Revises: 5ba730c9c123
Create Date: 2025-11-15 11:53:43.872629

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3004543fd24"
down_revision: str | Sequence[str] | None = "5ba730c9c123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add execution_id column (nullable, references task_executions)
    op.add_column("notification_sends", sa.Column("execution_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_notification_sends_execution_id",
        "notification_sends",
        "task_executions",
        ["execution_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add status column with default 'success'
    op.add_column(
        "notification_sends",
        sa.Column("status", sa.Text(), nullable=False, server_default="success"),
    )

    # Add error_message column (nullable)
    op.add_column("notification_sends", sa.Column("error_message", sa.Text(), nullable=True))

    # Rename sent_at to created_at for consistency
    op.alter_column("notification_sends", "sent_at", new_column_name="created_at")


def downgrade() -> None:
    """Downgrade schema."""
    # Rename created_at back to sent_at
    op.alter_column("notification_sends", "created_at", new_column_name="sent_at")

    # Drop added columns
    op.drop_column("notification_sends", "error_message")
    op.drop_column("notification_sends", "status")
    op.drop_constraint(
        "fk_notification_sends_execution_id", "notification_sends", type_="foreignkey"
    )
    op.drop_column("notification_sends", "execution_id")
