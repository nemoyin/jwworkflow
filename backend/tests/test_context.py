import pytest
from app.engine.context import ExecutionContext


class TestExecutionContext:
    def test_set_and_get(self):
        """验证设置和获取节点输出"""
        ctx = ExecutionContext({"query": "test"})
        ctx.set("n1", {"result": "hello"})
        assert ctx.get("n1") == {"result": "hello"}

    def test_get_nonexistent_node(self):
        """验证获取不存在的节点抛出 KeyError"""
        ctx = ExecutionContext({})
        with pytest.raises(KeyError):
            ctx.get("nonexistent")

    def test_resolve_simple_variable(self):
        """验证解析 {{ n1.output.field }} 变量"""
        ctx = ExecutionContext({"input_text": "world"})
        ctx.set("n1", {"summary": "hello world"})
        result = ctx.resolve_variable("{{ n1.summary }}")
        assert result == "hello world"

    def test_resolve_input_variable(self):
        """验证解析 {{ input.field }} 变量"""
        ctx = ExecutionContext({"query": "test_query"})
        result = ctx.resolve_variable("{{ input.query }}")
        assert result == "test_query"

    def test_resolve_nested_field(self):
        """验证解析嵌套字段"""
        ctx = ExecutionContext({})
        ctx.set("n1", {"data": {"score": 0.95, "label": "合规"}})
        result = ctx.resolve_variable("{{ n1.data.score }}")
        assert result == 0.95

    def test_get_inputs(self):
        """验证获取原始输入"""
        ctx = ExecutionContext({"query": "test"})
        assert ctx.inputs == {"query": "test"}
