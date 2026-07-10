import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    display_name: Mapped[str] = Column(String(128), default="")
    role: Mapped[str] = Column(String(32), default="member")  # admin | member
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tenant = relationship("Tenant", backref="users")

    def __init__(self, **kwargs: object) -> None:
        """Provide Python-level defaults for optional fields."""
        kwargs.setdefault("display_name", "")
        kwargs.setdefault("role", "member")
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
