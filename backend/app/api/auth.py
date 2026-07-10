"""Authentication endpoints: register and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新租户和管理员用户"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="邮箱已注册")

    # 创建租户
    tenant = Tenant(name=req.tenant_name, slug=req.tenant_name[:64])
    db.add(tenant)
    await db.flush()

    # 创建管理员用户
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=hash_password(req.password),
        display_name=req.email.split("@")[0],
        role="admin",
    )
    db.add(user)
    await db.flush()

    # 生成 token
    token = create_access_token(
        {"sub": str(user.id), "tenant_id": str(tenant.id)}
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = create_access_token(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    return TokenResponse(access_token=token)
