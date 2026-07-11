"""add workflow template model

Revision ID: f8c9d0e1f2a3
Revises: f7b2c1d3e4f5
Create Date: 2026-07-11 22:00:00.000000

Creates the ``workflow_templates`` table for pre-built workflow
templates that can be instantiated into user workflows.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "f8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "f7b2c1d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "workflow_templates",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=True),
        sa.Column("dag_definition", sa.JSON(), nullable=False),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("workflow_templates")
