import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, default="")
    type: Mapped[str] = Column(String(32), default="workflow")  # workflow | chatflow
    dag_definition: Mapped[dict] = Column(JSON, nullable=False)
    version: Mapped[int] = Column(Integer, default=1)
    status: Mapped[str] = Column(String(32), default="draft")  # draft | published
    created_by: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
