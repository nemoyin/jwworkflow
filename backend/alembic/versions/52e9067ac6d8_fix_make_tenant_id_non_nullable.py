"""fix: make tenant_id non-nullable

Revision ID: 52e9067ac6d8
Revises: 6b66573df82a
Create Date: 2026-07-11 06:58:14.573802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52e9067ac6d8'
down_revision: Union[str, Sequence[str], None] = '6b66573df82a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make tenant_id non-nullable (the existing migration assumes all rows have
    # a valid tenant_id since the column was always semantically required).
    op.alter_column("users", "tenant_id", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "tenant_id", nullable=True)
