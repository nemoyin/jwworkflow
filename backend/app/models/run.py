import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    triggered_by: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = Column(String(32), default="running")  # running | success | failed
    input: Mapped[dict] = Column(JSON, default=dict)
    output: Mapped[dict] = Column(JSON, default=dict)
    error: Mapped[str] = Column(Text, nullable=True)
    duration_ms: Mapped[int] = Column(Integer, nullable=True)
    node_results: Mapped[list] = Column(JSON, nullable=True)
    total_tokens: Mapped[int] = Column(Integer, default=0)
    model_used: Mapped[str] = Column(String(128), default="")
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
