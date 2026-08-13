import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRunsAPI:
    """运行历史 API 测试"""

    @pytest.fixture(scope="class")
    def token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "历史测试",
            "email": "history_test@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def workflow_id(self, headers):
        resp = client.post("/api/workflows", json={
            "name": "历史测试工作流",
            "description": "用于测试运行历史",
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
        }, headers=headers)
        return resp.json()["id"]

    @pytest.fixture
    def code_workflow_id(self, headers):
        """一个输出 numpy/pandas 类型的代码节点工作流（复现 服务端异常）"""
        resp = client.post("/api/workflows", json={
            "name": "Numpy代码工作流",
            "description": "代码节点输出 numpy 类型，验证持久化与响应不崩溃",
            "type": "workflow",
            "dag_definition": {
                "nodes": [
                    {"id": "n1", "type": "input", "config": {"fields": [{"name": "query", "type": "text"}]}},
                    {
                        "id": "n2", "type": "code", "config": {
                            "code": (
                                "import numpy as np\n"
                                "result = {'total': np.int64(42), "
                                "'avg': np.float64(1.5), "
                                "'date': np.datetime64('2025-01-01')}"
                            )
                        }
                    },
                    {"id": "n3", "type": "output", "config": {"variables": [{"name": "analysis", "source": "n2"}]}},
                ],
                "edges": [
                    {"id": "e1", "source": "n1", "target": "n2"},
                    {"id": "e2", "source": "n2", "target": "n3"},
                ]
            }
        }, headers=headers)
        assert resp.status_code in (200, 201), resp.text
        return resp.json()["id"]

    def test_run_code_node_with_numpy_output(self, headers, code_workflow_id):
        """代码节点输出 numpy 类型时，运行接口必须正常返回（不报 500/服务端异常）"""
        resp = client.post(
            f"/api/workflows/{code_workflow_id}/run",
            json={"query": "多维度分析销售数据"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text[:500]
        result = resp.json()["result"]
        assert result["analysis"]["total"] == 42
        assert result["analysis"]["avg"] == 1.5
        assert result["analysis"]["date"] == "2025-01-01"

    def test_list_runs_empty(self, headers):
        """验证运行历史为空时返回空列表"""
        resp = client.get("/api/runs", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_runs_after_run(self, headers, workflow_id):
        """验证执行工作流后运行历史列表有记录"""
        # 先执行工作流
        client.post(f"/api/workflows/{workflow_id}/run",
                    json={"query": "World"}, headers=headers)

        resp = client.get("/api/runs", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["workflow_id"] == workflow_id
        assert data[0]["workflow_name"] == "历史测试工作流"
        assert data[0]["status"] in ("success", "failed")
        assert "duration_ms" in data[0]
        assert "created_at" in data[0]

    def test_get_run_detail(self, headers, workflow_id):
        """验证获取运行详情"""
        # 执行工作流
        run_resp = client.post(f"/api/workflows/{workflow_id}/run",
                               json={"query": "Detail"}, headers=headers)
        run_id = run_resp.json()["id"]

        resp = client.get(f"/api/runs/{run_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == run_id
        assert data["workflow_id"] == workflow_id
        assert data["workflow_name"] == "历史测试工作流"
        assert data["status"] == "success"
        assert data["input"] == {"query": "Detail"}
        assert "output" in data
        assert data["duration_ms"] is not None
        assert data["node_results"] is not None
        assert "created_at" in data

    def test_get_run_detail_not_found(self, headers):
        """验证获取不存在的运行记录返回 404"""
        resp = client.get("/api/runs/00000000-0000-0000-0000-000000000000", headers=headers)
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_list_runs_tenant_isolation(self, headers, workflow_id):
        """验证不同租户之间运行历史隔离"""
        # 另一租户注册
        other_resp = client.post("/api/auth/register", json={
            "tenant_name": "其他租户",
            "email": "other_history@test.com",
            "password": "Test123!@#"
        })
        other_token = other_resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # 当前租户有记录，新租户应该为空
        resp = client.get("/api/runs", headers=other_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_run_detail_unauthorized(self, headers, workflow_id):
        """验证未授权访问返回 401"""
        resp = client.get("/api/runs")
        assert resp.status_code in (401, 403)

    def test_get_run_detail_invalid_id(self, headers):
        """验证无效 ID 返回 400"""
        resp = client.get("/api/runs/invalid-uuid", headers=headers)
        assert resp.status_code == 400
        assert "无效" in resp.json()["detail"]
