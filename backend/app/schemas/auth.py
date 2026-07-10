"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    tenant_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    tenant_id: str
