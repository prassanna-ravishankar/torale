"""auto verify clerk emails

Revision ID: 9fb326d5f5a7
Revises: fc5af45d5080
Create Date: 2025-11-09 19:19:55.761403

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "9fb326d5f5a7"
down_revision: str | Sequence[str] | None = "fc5af45d5080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
