import pytest
from app.engine.context import ExecutionContext
from app.nodes.output_node import OutputNodeExecutor


class TestOutputNode:
    def test_output_returns_selected_variables(self):
        """验证输出节点返回选中的变量"""
        executor = OutputNodeExecutor()
        ctx = ExecutionContext({"query": "test"})
        ctx.set("n1", {"result": "hello", "score": 0.95})
        config = {"variables": [{"name": "result", "source": "n1.result"}]}
        result = executor.execute(ctx, config)
        assert result == {"result": "hello"}
