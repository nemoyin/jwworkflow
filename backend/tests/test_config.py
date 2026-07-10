import os

import pytest
from app.config import Settings


class TestSettings:
    def test_default_database_url(self):
        """验证默认 DATABASE_URL 存在"""
        settings = Settings(DATABASE_URL="postgresql://postgres:postgres@localhost:5432/jwworkflow")
        assert settings.DATABASE_URL is not None
        assert "postgresql" in settings.DATABASE_URL

    def test_jwt_secret_required(self, monkeypatch):
        """验证 JWT_SECRET 必须设置"""
        monkeypatch.delenv("JWT_SECRET", raising=False)
        with pytest.raises(Exception):
            Settings()  # 缺 JWT_SECRET 应该报错
