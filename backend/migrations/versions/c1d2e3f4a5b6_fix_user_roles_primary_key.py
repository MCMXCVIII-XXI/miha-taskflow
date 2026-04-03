"""fix user_roles primary key

Revision ID: c1d2e3f4a5b6
Revises: bfe899dccc6e
Create Date: 2026-04-02 21:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "bfe899dccc6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old primary key constraint
    op.drop_constraint("user_roles_pkey", "user_roles", type_="primary")

    # Create new primary key on id column
    op.create_primary_key("user_roles_pkey", "user_roles", ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new primary key
    op.drop_constraint("user_roles_pkey", "user_roles", type_="primary")

    # Restore old primary key
    op.create_primary_key("user_roles_pkey", "user_roles", ["user_id", "role_id"])
