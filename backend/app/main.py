import logging as _logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth as auth_router
from app.api import workflows as workflows_router
from app.api import runs as runs_router
from app.api import knowledge as knowledge_router
from app.api import conversations as conversations_router
from app.api import templates as templates_router
from app.api import models as models_router
from app.api import admin as admin_router
from app.api import webhooks as webhooks_router
from app.api import dsl as dsl_router
from app.api import analytics as analytics_router
from app.api import mcp as mcp_router
from app.api import tools as tools_router
from app.api import workflow_upload as workflow_upload_router
from app.api import logs as logs_router
from app.api import workflow_stream as workflow_stream_router
from app.config import settings
from app.database import engine, Base

# ---------------------------------------------------------------------------
# Register logging middleware & error handlers
# ---------------------------------------------------------------------------
from app.middleware.logging import (
    RequestLogMiddleware,
    global_exception_handler,
    http_exception_handler,
)

_logging.getLogger("jwworkflow").info("=" * 60)
_logging.getLogger("jwworkflow").info("  jwworkflow starting…")
_logging.getLogger("jwworkflow").info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用启动和关闭时的资源生命周期。

    启动时: 创建所有尚未存在的数据库表（开发环境用）。
    关闭时: 释放数据库连接池。
    """
    from app.models import Tenant, User, Workflow, Run, Document, Embedding, Conversation, Message, WorkflowTemplate, ModelProvider, ModelRegistry  # noqa: F401
    async with engine.begin() as conn:
        try:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            pass
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

# Request logging middleware（放在 CORS 之后以记录真实响应状态）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLogMiddleware)

# Global exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(auth_router.router)
app.include_router(workflows_router.router)
app.include_router(runs_router.router)
app.include_router(knowledge_router.router)
app.include_router(conversations_router.router)
app.include_router(templates_router.router)
app.include_router(models_router.router)
app.include_router(admin_router.router)
app.include_router(webhooks_router.router)
app.include_router(dsl_router.router)
app.include_router(analytics_router.router)
app.include_router(mcp_router.router)
app.include_router(tools_router.router)
app.include_router(workflow_upload_router.router)
app.include_router(logs_router.router)
app.include_router(workflow_stream_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
