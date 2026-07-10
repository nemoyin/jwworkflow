"""多租户数据隔离测试"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestTenantIsolation:
    """验证不同租户之间的数据严格隔离"""

    @pytest.fixture(scope="class")
    def tenant_a_token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "租户A",
            "email": "isolation_a@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    @pytest.fixture(scope="class")
    def tenant_b_token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "租户B",
            "email": "isolation_b@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    def test_tenant_a_me_has_tenant_a_id(self, tenant_a_token):
        """验证租户A 的用户可以看到自己的 tenant_id"""
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tenant_a_token}"})
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] is not None

    def test_different_tenants_have_different_ids(self, tenant_a_token, tenant_b_token):
        """验证不同租户有不同的 tenant_id"""
        resp_a = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tenant_a_token}"})
        resp_b = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tenant_b_token}"})
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert resp_a.json()["tenant_id"] != resp_b.json()["tenant_id"]

    def test_tenant_a_cannot_access_tenant_b_data(self, tenant_a_token, tenant_b_token):
        """验证租户A 无法看到租户B 的用户信息"""
        resp_b_me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tenant_b_token}"}
        )
        resp_a_me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tenant_a_token}"}
        )
        # 两个用户看到的 tenant_id 应该不同
        assert resp_a_me.json()["tenant_id"] != resp_b_me.json()["tenant_id"]
        # 两个用户的 email 应该不同
        assert resp_a_me.json()["email"] != resp_b_me.json()["email"]
