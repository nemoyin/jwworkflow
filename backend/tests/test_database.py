import os

import pytest
from sqlalchemy import text


class TestDatabase:
    def test_engine_creation(self):
        """验证数据库引擎可以创建"""
        from app.database import engine

        assert engine is not None

    @pytest.mark.asyncio
    async def test_db_session(self):
        """验证数据库会话可以建立连接"""
        from app.database import get_db

        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            break  # 只测试一次连接
