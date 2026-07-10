"""Tests for Tenant and User ORM models."""

from app.models.tenant import Tenant
from app.models.user import User


class TestTenantModel:
    def test_tenant_creation(self):
        """验证 Tenant 模型可以实例化"""
        tenant = Tenant(name="测试租户", slug="test-tenant")
        assert tenant.name == "测试租户"
        assert tenant.slug == "test-tenant"
        assert tenant.plan == "free"  # 默认值

    def test_tenant_repr(self):
        """验证 Tenant __repr__"""
        tenant = Tenant(name="租户", slug="my-tenant")
        assert repr(tenant) == "<Tenant my-tenant>"


class TestUserModel:
    def test_user_creation(self):
        """验证 User 模型可以实例化"""
        user = User(
            email="test@example.com",
            password_hash="hashed_pwd",
            role="member",
        )
        assert user.email == "test@example.com"
        assert user.role == "member"
        assert user.is_active is True  # 默认值

    def test_user_repr(self):
        """验证 User __repr__"""
        user = User(
            email="user@test.com",
            password_hash="pwd",
            role="admin",
        )
        assert repr(user) == "<User user@test.com>"
