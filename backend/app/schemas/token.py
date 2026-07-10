"""Pydantic schemas for JWT token."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
