"""add model provider and registry tables

Revision ID: 4a8bba3bf0a3
Revises: f8c9d0e1f2a3
Create Date: 2026-07-11 14:05:59.320049
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8bba3bf0a3'
down_revision: Union[str, Sequence[str], None] = 'f8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # model_providers
    op.create_table('model_providers',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('provider_type', sa.String(64), nullable=False, server_default='openai'),
        sa.Column('api_key', sa.String(512), nullable=False, server_default=''),
        sa.Column('base_url', sa.String(512), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # model_registry
    op.create_table('model_registry',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('provider_id', sa.String(36), nullable=False),
        sa.Column('model_name', sa.String(128), nullable=False),
        sa.Column('display_name', sa.String(256), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provider_id'], ['model_providers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('model_registry')
    op.drop_table('model_providers')
