"""LLM 供应商/提供商 ORM 模型"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from app.database import Base


class ModelProvider(Base):
    """LLM 供应商配置"""

    __tablename__ = "model_providers"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = Column(String(128), nullable=False)
    provider_type: Mapped[str] = Column(String(64), nullable=False, default="openai")
    api_key: Mapped[str] = Column(String(512), nullable=False, default="")
    base_url: Mapped[str] = Column(String(512), nullable=False, default="")
    is_active: Mapped[bool] = Column(Boolean, default=True)
    sort_order: Mapped[int] = Column(Integer, default=0)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    models = relationship("ModelRegistry", backref="provider", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ModelProvider {self.name} ({self.provider_type})>"
