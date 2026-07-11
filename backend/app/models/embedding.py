"""Embedding ORM model with pgvector support.

Stores document chunk embeddings for vector similarity search.
Uses pgvector's VECTOR(1536) type on PostgreSQL, falls back to
TEXT on SQLite (testing) via a TypeDecorator.
"""

import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped

from app.database import Base


class Vector(TypeDecorator):
    """Cross-dialect vector type.

    On PostgreSQL this delegates to pgvector's ``Vector(1536)`` type.
    On SQLite (testing) it stores the list-of-floats as JSON text.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector as PgVector

                return dialect.type_descriptor(PgVector(1536))
            except ImportError:
                pass  # fall through to text storage
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if dialect.name != "postgresql" and value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != "postgresql" and value is not None:
            return json.loads(value)
        return value


class Embedding(Base):
    """A single text chunk and its embedding vector for a document."""

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    chunk_index: Mapped[int] = Column(Integer, nullable=False)
    chunk_text: Mapped[str] = Column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = Column(
        Vector(), nullable=True  # type: ignore[arg-type]
    )
    tenant_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
