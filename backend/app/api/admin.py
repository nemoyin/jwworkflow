"""租户管理 + 用户管理 (仅 admin)"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.rbac import admin_required
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from app.services.auth_service import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ========== 租户管理 ==========

@router.get("/tenants")
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    """列出所有租户"""
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "plan": t.plan,
            "created_at": t.created_at.isoformat(),
        }
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}")
async def get_tenant_detail(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    """租户详情（含用户列表）"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    users_result = await db.execute(
        select(User).where(User.tenant_id == tenant.id)
    )
    users = users_result.scalars().all()

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "plan": tenant.plan,
        "config": tenant.config,
        "created_at": tenant.created_at.isoformat(),
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
    }


# ========== 用户管理（本租户内） ==========

@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前租户的所有用户"""
    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.post("/users", status_code=201)
async def invite_user(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """邀请用户（添加成员到当前租户）"""
    email = body.get("email", "")
    role = body.get("role", "member")
    password = body.get("password", "Default123!@#")

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="邮箱已注册")

    user = User(
        tenant_id=current_user.tenant_id,
        email=email,
        password_hash=hash_password(password),
        display_name=email.split("@")[0],
        role=role,
    )
    db.add(user)
    await db.flush()

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户信息（角色、状态）"""
    result = await db.execute(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if "role" in body:
        user.role = body["role"]
    if "is_active" in body:
        user.is_active = body["is_active"]
    if "display_name" in body:
        user.display_name = body["display_name"]
    await db.flush()

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除用户"""
    result = await db.execute(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    await db.delete(user)
    await db.flush()
