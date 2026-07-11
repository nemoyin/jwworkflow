"""RBAC 权限控制中间件"""

from fastapi import Depends, HTTPException, status
from app.middleware.auth_middleware import get_current_user
from app.models.user import User


async def admin_required(current_user: User = Depends(get_current_user)) -> User:
    """要求当前用户为 admin 角色"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def member_required(current_user: User = Depends(get_current_user)) -> User:
    """要求当前用户为 member 或 admin 角色"""
    if current_user.role not in ("admin", "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user
