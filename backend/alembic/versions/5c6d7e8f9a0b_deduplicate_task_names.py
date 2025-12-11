"""deduplicate_task_names

Revision ID: 5c6d7e8f9a0b
Revises: a1b2c3d4e5f6
Create Date: 2025-12-11 16:30:00.000000

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "5c6d7e8f9a0b"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """De-duplicate task names for the same user before adding unique constraint."""
    connection = op.get_bind()

    # Find all duplicate (user_id, name) combinations
    duplicates_query = text("""
        SELECT user_id, name, array_agg(id ORDER BY created_at) as task_ids
        FROM tasks
        GROUP BY user_id, name
        HAVING COUNT(*) > 1
    """)

    duplicates = connection.execute(duplicates_query).fetchall()

    # For each set of duplicates, keep the first one and rename the rest
    for row in duplicates:
        user_id, name, task_ids = row
        # Skip the first task (keep original name), rename the rest
        for idx, task_id in enumerate(task_ids[1:], start=2):
            new_name = f"{name} ({idx})"
            connection.execute(
                text("UPDATE tasks SET name = :new_name WHERE id = :task_id"),
                {"new_name": new_name, "task_id": task_id}
            )


def downgrade() -> None:
    """No downgrade needed - we don't restore duplicate names."""
    pass
