import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestWorkflowAPI:
    """工作流 CRUD + 运行 API 测试"""

    @pytest.fixture(scope="class")
    def token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "工作流测试",
            "email": "wf_test@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def sample_workflow(self):
        return {
            "name": "测试工作流",
            "description": "一个简单的测试工作流",
            "type": "workflow",
            "dag_definition": {
                "nodes": [
                    {"id": "n1", "type": "input", "config": {"fields": [{"name": "query", "type": "text"}]}},
                    {"id": "n2", "type": "template", "config": {"template": "Hello {{ input.query }}"}},
                    {"id": "n3", "type": "output", "config": {"variables": [{"name": "greeting", "source": "n2.output"}]}},
                ],
                "edges": [
                    {"id": "e1", "source": "n1", "target": "n2"},
                    {"id": "e2", "source": "n2", "target": "n3"},
                ]
            }
        }

    def test_create_workflow(self, headers, sample_workflow):
        """验证创建工作流"""
        resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "测试工作流"
        assert "id" in data

    def test_list_workflows(self, headers):
        """验证获取工作流列表"""
        resp = client.get("/api/workflows", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_workflow(self, headers, sample_workflow):
        """验证获取工作流详情"""
        create_resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        wf_id = create_resp.json()["id"]

        resp = client.get(f"/api/workflows/{wf_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "测试工作流"

    def test_run_workflow(self, headers, sample_workflow):
        """验证执行工作流返回结果"""
        create_resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        wf_id = create_resp.json()["id"]

        resp = client.post(f"/api/workflows/{wf_id}/run",
                           json={"query": "World"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert data["result"] == {"greeting": "Hello World"}

    def test_delete_workflow(self, headers, sample_workflow):
        """验证删除工作流"""
        create_resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        wf_id = create_resp.json()["id"]

        resp = client.delete(f"/api/workflows/{wf_id}", headers=headers)
        assert resp.status_code == 204
