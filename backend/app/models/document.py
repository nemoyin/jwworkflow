import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    file_path: Mapped[str] = Column(String(512), nullable=False)
    content: Mapped[str] = Column(Text, nullable=True)
    content_type: Mapped[str] = Column(String(128), default="application/octet-stream")
    file_size: Mapped[int] = Column(Integer, default=0)
    status: Mapped[str] = Column(String(32), default="pending")  # pending | processing | ready | failed
    error: Mapped[str] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
