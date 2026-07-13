"""Tests for JWT authentication middleware and tenant isolation.

Verifies:
1. /me endpoint returns user info with a valid token
2. /me returns 401 without a token
3. /me returns 401 with an invalid token
4. Two different tenants produce different tenant_ids (tenant isolation)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.models.tenant import Tenant
from app.models.user import User

client = TestClient(app)


class TestAuthMiddleware:
    """Authentication middleware tests — token required for /me."""

    REGISTER_DATA_A = {
        "tenant_name": "甲有限公司",
        "email": "tenant_a@test.com",
        "password": "Pass123!@#",
    }
    REGISTER_DATA_B = {
        "tenant_name": "乙有限公司",
        "email": "tenant_b@test.com",
        "password": "Pass456!@#",
    }

    # ------------------------------------------------------------------
    # Class-level cleanup: remove test users/tenants so the suite is
    # idempotent (can be re-run without a DB reset).
    # ------------------------------------------------------------------

    @pytest.fixture(scope="class", autouse=True)
    async def _cleanup(cls):
        """Delete test users and tenants after all class tests complete."""
        yield
        from app.database import async_session

        emails = [cls.REGISTER_DATA_A["email"], cls.REGISTER_DATA_B["email"]]
        async with async_session() as session:
            await session.execute(
                delete(User).where(User.email.in_(emails))
            )
            await session.execute(
                delete(Tenant).where(
                    Tenant.name.in_(
                        [
                            cls.REGISTER_DATA_A["tenant_name"],
                            cls.REGISTER_DATA_B["tenant_name"],
                        ]
                    )
                )
            )
            await session.commit()

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture(scope="class")
    def token_a(self):
        """Register tenant A and return its access token."""
        resp = client.post("/api/auth/register", json=self.REGISTER_DATA_A)
        assert resp.status_code == 201
        return resp.json()["access_token"]

    @pytest.fixture(scope="class")
    def token_b(self):
        """Register tenant B and return its access token."""
        resp = client.post("/api/auth/register", json=self.REGISTER_DATA_B)
        assert resp.status_code == 201
        return resp.json()["access_token"]

    # ------------------------------------------------------------------
    # Tests — /me  endpoint
    # ------------------------------------------------------------------

    def test_me_with_valid_token(self, token_a):
        """A valid token returns 200 with user info."""
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == self.REGISTER_DATA_A["email"]
        assert "tenant_id" in data
        assert "id" in data
        assert "role" in data

    def test_me_without_token(self):
        """No token returns 401."""
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    def test_me_with_invalid_token(self):
        """An invalid (garbage) token returns 401."""
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code in (401, 403)

    # ------------------------------------------------------------------
    # Tests — tenant isolation
    # ------------------------------------------------------------------

    def test_tenant_isolation_different_ids(self, token_a, token_b):
        """Two different tenants have different tenant_ids."""
        resp_a = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        resp_b = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        tenant_id_a = resp_a.json()["tenant_id"]
        tenant_id_b = resp_b.json()["tenant_id"]

        assert tenant_id_a != tenant_id_b, (
            f"Tenant isolation violated: both tokens returned "
            f"tenant_id={tenant_id_a}"
        )

    def test_tenant_isolation_same_tenant(self, token_a):
        """Calling /me twice with the same token returns the same tenant_id."""
        resp_1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        resp_2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})

        assert resp_1.status_code == 200
        assert resp_2.status_code == 200

        assert resp_1.json()["tenant_id"] == resp_2.json()["tenant_id"]

    def test_tenant_b_has_correct_email(self, token_b):
        """Token for tenant B returns tenant B's email."""
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == self.REGISTER_DATA_B["email"]
