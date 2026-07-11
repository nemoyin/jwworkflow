import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class Conversation(Base):
    """Multi-turn chat conversation.

    Each conversation is bound to a workflow and persists variables
    across turns so that later messages can reference earlier results.
    """

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    title: Mapped[str] = Column(String(255), default="New conversation")
    status: Mapped[str] = Column(
        String(32), default="active"
    )  # active | closed
    variables: Mapped[dict] = Column(
        JSON, default=dict
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Message(Base):
    """A single message within a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = Column(
        String(32), nullable=False
    )  # user | assistant | system
    content: Mapped[str] = Column(Text, nullable=False)
    extra_data: Mapped[dict] = Column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
