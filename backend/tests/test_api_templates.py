import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.context import ExecutionContext

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
        assert "小升初择优面试" in names
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

    def _xsc_template(self, headers):
        resp = client.get("/api/templates", headers=headers)
        return next(t for t in resp.json() if t["name"] == "小升初择优面试")

    def test_xsc_template_structure(self, headers):
        """验证「小升初择优面试」模板结构：输入字段 + chat agent + 输出节点"""
        tpl = self._xsc_template(headers)
        dag = tpl["dag_definition"]
        nodes = {n["id"]: n for n in dag["nodes"]}

        assert tpl["category"] == "interview"

        # input 节点：school_info / student_info / interview_mode
        fields = nodes["n1"]["config"]["fields"]
        names = [f["name"] for f in fields]
        assert names == ["school_info", "student_info", "interview_mode"]
        im = next(f for f in fields if f["name"] == "interview_mode")
        assert im["default"] == "adaptive"
        assert [o["value"] for o in im["options"]] == [
            "adaptive", "normal", "elite", "pressure",
            "academic", "logic", "expression", "comprehensive",
        ]

        # agent 节点：chat 模式，提示词引用全部输入变量
        agent = nodes["n2"]["config"]
        assert agent["mode"] == "chat"
        assert agent["model"] == "deepseek-chat"
        assert "{{ input.school_info }}" in agent["system_prompt"]
        assert "{{ input.student_info }}" in agent["system_prompt"]
        assert "{{ input.interview_mode }}" in agent["system_prompt"]

        # output 节点：conversation_log ← n2.output
        out = nodes["n3"]["config"]["variables"]
        assert out == [{"name": "conversation_log", "source": "n2.output"}]

        assert dag["edges"] == [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ]

    def test_instantiate_xsc_interview_chatflow(self, headers):
        """验证从「小升初择优面试」模板创建 chatflow 工作流且 interview_mode=True"""
        tpl = self._xsc_template(headers)
        inst_resp = client.post(
            f"/api/templates/{tpl['id']}/instantiate",
            json={"name": "盐道街小升初择优面试"},
            headers=headers,
        )
        assert inst_resp.status_code == 200
        wf_id = inst_resp.json()["workflow_id"]

        wf_resp = client.get(f"/api/workflows/{wf_id}", headers=headers)
        assert wf_resp.status_code == 200
        assert wf_resp.json()["type"] == "chatflow"

        # preview 暴露输入字段与数字人访谈能力
        prev_resp = client.get(f"/api/workflows/{wf_id}/preview", headers=headers)
        assert prev_resp.status_code == 200
        prev = prev_resp.json()
        assert prev["interview_mode"] is True
        fields = {f["name"] for f in prev["input_fields"]}
        assert {"school_info", "student_info", "interview_mode"} <= fields

    def test_xsc_prompt_resolves_input_variables(self, headers):
        """验证 chat agent 的 system_prompt 能渲染 {{ input.xxx }} 变量"""
        tpl = self._xsc_template(headers)
        dag = tpl["dag_definition"]
        agent = next(n for n in dag["nodes"] if n["type"] == "agent")
        system_prompt = agent["config"]["system_prompt"]

        inputs = {
            "school_info": "成都市盐道街中学初中部，重视综合素养与学科基础，实验班重点考察数学思维",
            "student_info": "小明，就读于盐道街小学，数学竞赛市级二等奖，热爱阅读",
            "interview_mode": "elite",
        }
        rendered = ExecutionContext(inputs=inputs).resolve_variable(system_prompt)
        assert "{{ input.school_info }}" not in rendered
        assert "成都市盐道街中学初中部" in rendered
        assert "{{ input.student_info }}" not in rendered
        assert "小明" in rendered
        assert "{{ input.interview_mode }}" not in rendered
        assert "elite" in rendered
