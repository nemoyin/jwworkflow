"""请求日志中间件 + 全局异常处理器 + 错误日志环形缓冲区。

增强内容：
  - 控制台同时输出 DEBUG 和 ERROR 级别
  - 所有 4xx/5xx 响应记入错误缓冲区
  - 每条错误记录包含：request_id / 完整 traceback / query params
  - 文件日志使用绝对路径，确保始终可写
"""

import logging
import os
import time
import uuid
import traceback
from collections import deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ---------------------------------------------------------------------------
# 错误日志环形缓冲区（线程安全，最多保留 500 条）
# ---------------------------------------------------------------------------
ERROR_LOG: deque[dict] = deque(maxlen=500)
_error_lock = Lock()


def record_error(
    request_id: str,
    method: str,
    path: str,
    status: int,
    message: str,
    detail: str = "",
    stack: str = "",
    query: str = "",
):
    with _error_lock:
        ERROR_LOG.append({
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "method": method,
            "path": path,
            "query": query,
            "status": status,
            "message": message,
            "detail": detail,
            "stack": stack[:3000],
        })


def get_recent_errors(limit: int = 50) -> list[dict]:
    with _error_lock:
        return list(ERROR_LOG)[-limit:]


# ---------------------------------------------------------------------------
# 日志记录器 — 双重输出：控制台高亮 + 文件持久
# ---------------------------------------------------------------------------
logger = logging.getLogger("jwworkflow")
logger.setLevel(logging.DEBUG)

# 防止重复添加 handler
if not logger.handlers:
    # ---- Console handler: INFO+, 错误用 ERROR 级别显示 ----
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-5s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(console)

    # ---- File handler: 全部级别，含 DEBUG ----
    # 优先使用绝对路径，确保始终可写
    _log_dir = os.path.dirname(os.path.abspath(__file__))  # app/middleware/
    _log_dir = os.path.join(_log_dir, "..", "..")           # backend/
    _log_path = os.path.abspath(os.path.join(_log_dir, "backend.log"))
    try:
        fh = logging.FileHandler(_log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-5s  %(name)s  |  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(fh)
        logger.info("Log file: %s", _log_path)
    except Exception as e:
        logger.warning("Cannot create log file %s: %s", _log_path, e)


# ---------------------------------------------------------------------------
# 工具：提取 request body（只对 5xx 记录，避免敏感数据泄漏）
# ---------------------------------------------------------------------------
async def _get_request_body(request: Request) -> str:
    """安全地提取请求 body 的前 500 字节。"""
    try:
        body = await request.body()
        return body[:500].decode("utf-8", errors="replace")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# 中间件
# ---------------------------------------------------------------------------
class RequestLogMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求的 method / path / status / duration / query / client_ip。"""

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.time()
        client_ip = request.client.host if request.client else "unknown"
        query_str = str(request.url.query) if request.url.query else ""

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start) * 1000)

            status = response.status_code
            if status >= 500:
                logger.error(
                    "%s %s %d %dms [%s] %s",
                    request.method, request.url.path, status, duration_ms, client_ip, request_id,
                )
                body_text = ""
                try:
                    body_text = (response.body or b"")[:500].decode("utf-8", errors="replace")
                except Exception:
                    pass
                record_error(
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status=status,
                    message=f"HTTP {status} on {request.method} {request.url.path}",
                    detail=body_text,
                    query=query_str,
                )
            elif status >= 400:
                logger.warning(
                    "%s %s %d %dms [%s] %s",
                    request.method, request.url.path, status, duration_ms, client_ip, request_id,
                )
                # 4xx 也写入错误缓冲区（方便调试）
                record_error(
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status=status,
                    message=f"HTTP {status} on {request.method} {request.url.path}",
                    query=query_str,
                )
            else:
                logger.info(
                    "%s %s %d %dms [%s] %s",
                    request.method, request.url.path, status, duration_ms, client_ip, request_id,
                )

            return response

        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            tb = traceback.format_exc()
            logger.error(
                "%s %s 500 %dms [%s] %s\n%s",
                request.method, request.url.path, duration_ms, client_ip, request_id, tb,
            )
            record_error(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=500,
                message=f"{type(exc).__name__}: {exc}",
                detail="Middleware unhandled exception",
                stack=tb,
                query=query_str,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "code": "INTERNAL_ERROR",
                    "message": f"服务器内部错误: {type(exc).__name__}: {exc}",
                    "request_id": request_id,
                },
            )


# ---------------------------------------------------------------------------
# 全局异常处理器
# ---------------------------------------------------------------------------
from fastapi import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException


async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex[:12])
    tb = traceback.format_exc()
    logger.error("Global handler [%s]: %s\n%s", request_id, exc, tb)
    record_error(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=500,
        message=f"GlobalHandler {type(exc).__name__}: {exc}",
        stack=tb,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": f"{type(exc).__name__}: {exc}",
            "request_id": request_id,
        },
    )


async def http_exception_handler(request: Request, exc):
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex[:12])
    status = exc.status_code
    detail = exc.detail if hasattr(exc, "detail") else str(exc)
    if status >= 500:
        logger.error("HTTP %d %s %s [%s]: %s", status, request.method, request.url.path, request_id, detail)
        record_error(
            request_id=request_id, method=request.method, path=request.url.path,
            status=status, message=str(detail)[:500], detail=str(detail),
        )
    elif status >= 400:
        logger.warning("HTTP %d %s %s [%s]: %s", status, request.method, request.url.path, request_id, detail)
        record_error(
            request_id=request_id, method=request.method, path=request.url.path,
            status=status, message=str(detail)[:200],
        )
    return JSONResponse(
        status_code=status,
        content={
            "error": True,
            "code": f"HTTP_{status}",
            "message": str(detail)[:500],
            "detail": str(detail),
            "request_id": request_id,
        },
    )
