"""Pydantic schemas for Tenant."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str
    slug: str
    plan: str = "free"


class TenantResponse(BaseModel):
    """Schema for tenant response."""

    id: UUID
    name: str
    slug: str
    plan: str
    config: dict
    created_at: datetime

    model_config = {"from_attributes": True}
