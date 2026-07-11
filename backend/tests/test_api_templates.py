import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestTemplateAPI:
    """模板市场 API 测试"""

    @pytest.fixture(scope="class")
    def token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "模板测试",
            "email": "tpl_test@test.com",
            "password": "Test123!@#",
        })
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_list_templates_returns_builtin_templates(self, headers):
        """验证 GET /api/templates 返回至少 4 个内置模板"""
        resp = client.get("/api/templates", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

        names = [t["name"] for t in data]
        assert "招标合规审查" in names
        assert "围串标分析" in names
        assert "纪检模拟谈话" in names
        assert "AI 问数" in names

    def test_list_templates_all_have_required_fields(self, headers):
        """验证每个模板都包含必要字段"""
        resp = client.get("/api/templates", headers=headers)
        assert resp.status_code == 200
        for t in resp.json():
            assert "id" in t
            assert "name" in t
            assert "category" in t
            assert "dag_definition" in t
            assert "is_builtin" in t
            assert "sort_order" in t

    def test_instantiate_tender_compliance_template(self, headers):
        """验证从「招标合规审查」模板创建工作流"""
        resp = client.get("/api/templates", headers=headers)
        templates = resp.json()
        tpl = next(t for t in templates if t["name"] == "招标合规审查")

        inst_resp = client.post(
            f"/api/templates/{tpl['id']}/instantiate",
            json={"name": "我的合规审查"},
            headers=headers,
        )
        assert inst_resp.status_code == 200
        data = inst_resp.json()
        assert "workflow_id" in data
        assert data["workflow_name"] == "我的合规审查"

        # 验证创建的工作流可被查询
        wf_resp = client.get(
            f"/api/workflows/{data['workflow_id']}",
            headers=headers,
        )
        assert wf_resp.status_code == 200
        assert wf_resp.json()["name"] == "我的合规审查"

    def test_instantiate_collusion_analysis_template(self, headers):
        """验证从「围串标分析」模板创建工作流"""
        resp = client.get("/api/templates", headers=headers)
        templates = resp.json()
        tpl = next(t for t in templates if t["name"] == "围串标分析")

        inst_resp = client.post(
            f"/api/templates/{tpl['id']}/instantiate",
            json={},
            headers=headers,
        )
        assert inst_resp.status_code == 200
        data = inst_resp.json()
        assert "workflow_id" in data
        assert "围串标分析" in data["workflow_name"]

    def test_instantiate_interview_chatflow(self, headers):
        """验证从「纪检模拟谈话」模板创建 chatflow 类型工作流"""
        resp = client.get("/api/templates", headers=headers)
        templates = resp.json()
        tpl = next(t for t in templates if t["name"] == "纪检模拟谈话")

        inst_resp = client.post(
            f"/api/templates/{tpl['id']}/instantiate",
            json={},
            headers=headers,
        )
        assert inst_resp.status_code == 200
        data = inst_resp.json()

        # 验证工作流的类型为 chatflow
        wf_resp = client.get(
            f"/api/workflows/{data['workflow_id']}",
            headers=headers,
        )
        assert wf_resp.status_code == 200
        assert wf_resp.json()["type"] == "chatflow"

    def test_instantiate_ai_ask_template(self, headers):
        """验证从「AI 问数」模板创建工作流"""
        resp = client.get("/api/templates", headers=headers)
        templates = resp.json()
        tpl = next(t for t in templates if t["name"] == "AI 问数")

        inst_resp = client.post(
            f"/api/templates/{tpl['id']}/instantiate",
            json={
                "name": "数据查询助手",
                "description": "用于日常数据查询分析",
            },
            headers=headers,
        )
        assert inst_resp.status_code == 200
        assert inst_resp.json()["workflow_name"] == "数据查询助手"

    def test_instantiate_nonexistent_template_returns_404(self, headers):
        """验证实例化不存在的模板返回 404"""
        resp = client.post(
            "/api/templates/nonexistent-id/instantiate",
            json={},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_list_templates_sorted_by_sort_order(self, headers):
        """验证模板按 sort_order 排序"""
        resp = client.get("/api/templates", headers=headers)
        data = resp.json()
        orders = [t["sort_order"] for t in data]
        assert orders == sorted(orders)
