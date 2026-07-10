"""FastAPI dependency for extracting the current user from JWT.

Also sets ``tenant_ctx_var`` so that downstream code can retrieve the current
tenant ID without re-parsing the JWT or re-querying the database.

Also provides ``get_current_tenant`` — a convenience dependency that uses
``Depends(get_current_user)`` to avoid duplicate JWT decode and DB queries.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.context import tenant_ctx_var
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_service import decode_access_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 解析当前用户并设置租户上下文"""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="无效的 token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="token 中缺少用户信息")

    # Convert string to uuid.UUID so SQLAlchemy can bind it correctly,
    # even when the database is SQLite (which doesn't natively support UUID).
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="token 中用户 ID 格式无效")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已禁用")

    # 设置租户上下文，供 tenant_middleware.get_tenant_id() 读取
    tenant_ctx_var.set(str(user.tenant_id))

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """从当前用户获取租户"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return tenant
