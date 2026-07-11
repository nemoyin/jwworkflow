from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth as auth_router
from app.api import workflows as workflows_router
from app.api import runs as runs_router
from app.api import knowledge as knowledge_router
from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用启动和关闭时的资源生命周期。

    启动时: 创建所有尚未存在的数据库表（开发环境用）。
    关闭时: 释放数据库连接池。
    """
    # 导入所有模型以确保 Base.metadata 已注册
    from app.models import Tenant, User, Workflow, Run, Document  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(workflows_router.router)
app.include_router(runs_router.router)
app.include_router(knowledge_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
