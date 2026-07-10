"""Pydantic schemas for User."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: str
    password: str
    display_name: str = ""
    role: str = "member"


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    tenant_id: UUID | None
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
