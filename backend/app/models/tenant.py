import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = Column(String(255), nullable=False)
    slug: Mapped[str] = Column(String(64), unique=True, nullable=False, index=True)
    plan: Mapped[str] = Column(String(32), default="free")
    config: Mapped[dict] = Column(JSON, default=dict)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __init__(self, **kwargs: object) -> None:
        """Provide Python-level defaults for optional fields."""
        kwargs.setdefault("plan", "free")
        kwargs.setdefault("config", {})
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"
