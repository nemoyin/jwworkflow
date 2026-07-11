import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, default="")
    category: Mapped[str] = Column(String(32), default="general")  # compliance | collusion | interview | chat | general
    dag_definition: Mapped[dict] = Column(JSON, nullable=False)
    icon: Mapped[str] = Column(String(64), default="")
    sort_order: Mapped[int] = Column(Integer, default=0)
    is_builtin: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
