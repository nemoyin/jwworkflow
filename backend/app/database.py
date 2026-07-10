from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _build_async_url() -> str:
    """将同步 DATABASE_URL 转换为异步兼容的 URL.

    - postgresql+psycopg2:// → postgresql+asyncpg://
    - 其他驱动（如 sqlite+aiosqlite）保持不变，方便测试环境使用 SQLite。
    """
    url = settings.DATABASE_URL
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    return url


async_db_url = _build_async_url()

engine = create_async_engine(async_db_url, echo=settings.DEBUG)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy ORM 基类，所有模型都应继承此类。"""

    pass


async def get_db():
    """FastAPI 依赖项：提供异步数据库会话。

    Yields:
        AsyncSession: 数据库会话，请求结束时自动提交或回滚。
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
