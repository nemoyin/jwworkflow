"""add embeddings model (pgvector)

Revision ID: a1b2c3d4e5f6
Revises: e43a8f02b1c0
Create Date: 2026-07-11 12:00:00.000000

Creates the ``embeddings`` table that stores document chunk text and
pgvector embeddings for RAG similarity search.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e43a8f02b1c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "embeddings",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("document_id", UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),  # vector(1536) at runtime
        sa.Column("tenant_id", UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create index on (tenant_id, document_id) for filtered retrieval
    op.create_index(
        "ix_embeddings_tenant_doc",
        "embeddings",
        ["tenant_id", "document_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_embeddings_tenant_doc")
    op.drop_table("embeddings")
