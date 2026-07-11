import pytest
from app.engine.context import ExecutionContext
from app.nodes.template_node import TemplateNodeExecutor


class TestTemplateNode:
    def test_template_renders_variables(self):
        """验证模板渲染变量"""
        executor = TemplateNodeExecutor()
        ctx = ExecutionContext({"query": "test"})
        ctx.set("n1", {"summary": "hello world"})
        config = {"template": "Result: {{ n1.summary }}, Query: {{ input.query }}"}
        result = executor.execute(ctx, config)
        assert result == {"output": "Result: hello world, Query: test"}

    def test_template_no_variables(self):
        """验证无变量模板原样输出"""
        executor = TemplateNodeExecutor()
        ctx = ExecutionContext({})
        config = {"template": "Plain text"}
        result = executor.execute(ctx, config)
        assert result == {"output": "Plain text"}
