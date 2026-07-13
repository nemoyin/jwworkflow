"""多模型管理 API 测试"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def token():
    import time
    resp = client.post("/api/auth/register", json={
        "tenant_name": "模型管理测试",
        "email": f"model_mgmt_{int(time.time())}@test.com",
        "password": "Test123!@#"
    })
    return resp.json()["access_token"]


@pytest.fixture
def h(token):
    return {"Authorization": f"Bearer {token}"}


def test_list_providers_empty(h):
    resp = client.get("/api/admin/providers", headers=h)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_update_provider(h):
    # Create
    resp = client.post("/api/admin/providers", json={
        "name": "DeepSeek", "provider_type": "deepseek",
        "api_key": "sk-test-key", "base_url": "https://api.deepseek.com",
    }, headers=h)
    assert resp.status_code == 201
    pid = resp.json()["id"]

    # Update
    resp = client.put(f"/api/admin/providers/{pid}", json={
        "base_url": "https://api.deepseek.com/v1",
    }, headers=h)
    assert resp.status_code == 200
    assert resp.json()["base_url"] == "https://api.deepseek.com/v1"

    # Create model under this provider
    resp = client.post("/api/admin/models", json={
        "provider_id": pid, "model_name": "deepseek-v4-pro",
        "display_name": "DeepSeek V4 Pro",
        "capabilities": {"tool_calls": True, "streaming": True, "max_tokens": 65536},
    }, headers=h)
    assert resp.status_code == 201
    mid = resp.json()["id"]
    assert resp.json()["model_name"] == "deepseek-v4-pro"

    # List models
    resp = client.get("/api/admin/models", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Available models
    resp = client.get("/api/admin/models/available", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert "label" in resp.json()[0]

    # Delete model
    resp = client.delete(f"/api/admin/models/{mid}", headers=h)
    assert resp.status_code == 204

    # Delete provider
    resp = client.delete(f"/api/admin/providers/{pid}", headers=h)
    assert resp.status_code == 204


def test_unauthorized():
    client.headers.clear()
    resp = client.get("/api/admin/providers")
    assert resp.status_code in (401, 403)
