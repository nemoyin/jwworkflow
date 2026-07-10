import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAuth:
    REGISTER_DATA = {
        "tenant_name": "测试公司",
        "email": "admin@test.com",
        "password": "Test123!@#"
    }

    def test_register_success(self):
        """验证注册成功返回 token"""
        response = client.post("/api/auth/register", json=self.REGISTER_DATA)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_success(self):
        """验证登录成功返回 token"""
        # 先注册
        client.post("/api/auth/register", json=self.REGISTER_DATA)
        # 再登录
        response = client.post("/api/auth/login", json={
            "email": self.REGISTER_DATA["email"],
            "password": self.REGISTER_DATA["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self):
        """验证错误密码返回 401"""
        client.post("/api/auth/register", json=self.REGISTER_DATA)
        response = client.post("/api/auth/login", json={
            "email": self.REGISTER_DATA["email"],
            "password": "wrong_password"
        })
        assert response.status_code == 401
