"""fix task_assignees assigned_at default

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-02 21:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add server_default for assigned_at
    op.alter_column("task_assignees", "assigned_at", server_default=sa.text("now()"))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove server_default
    op.alter_column("task_assignees", "assigned_at", server_default=None)
