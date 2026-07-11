"""模型注册表 ORM 模型"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class ModelRegistry(Base):
    """模型注册表——每个供应商下的可用模型"""

    __tablename__ = "model_registry"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = Column(String(128), nullable=False)  # API 使用的模型名
    display_name: Mapped[str] = Column(String(256), default="")    # 展示名称
    capabilities: Mapped[dict] = Column(JSON, default=dict)        # {"tool_calls": true, "streaming": true, "max_tokens": 4096}
    is_active: Mapped[bool] = Column(Boolean, default=True)
    sort_order: Mapped[int] = Column(Integer, default=0)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ModelRegistry {self.display_name or self.model_name}>"
