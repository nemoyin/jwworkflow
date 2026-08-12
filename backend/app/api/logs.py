"""日志和调试信息查询接口。"""

from fastapi import APIRouter, Depends, Query

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.middleware.logging import get_recent_errors, logger

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/errors")
async def list_errors(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """获取最近的服务端错误日志（环形缓冲区内）。"""
    return {"errors": get_recent_errors(limit)}


@router.get("/debug")
async def debug_info(
    current_user: User = Depends(get_current_user),
):
    """返回运行时调试信息（日志级别、路径等）。"""
    return {
        "log_level": logger.level,
        "log_handlers": [str(h) for h in logger.handlers],
        "error_buffer_size": len(get_recent_errors(999)),
    }
