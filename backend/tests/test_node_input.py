import pytest
from app.engine.context import ExecutionContext
from app.nodes.input_node import InputNodeExecutor


class TestInputNode:
    def test_input_returns_fields(self):
        """验证输入节点返回字段"""
        executor = InputNodeExecutor()
        ctx = ExecutionContext({"query": "hello", "file": None})
        config = {"fields": [{"name": "query", "type": "text"}]}
        result = executor.execute(ctx, config)
        assert result == {"query": "hello"}

    def test_input_empty_config(self):
        """验证空配置返回空字典"""
        executor = InputNodeExecutor()
        ctx = ExecutionContext({"query": "hello"})
        result = executor.execute(ctx, {"fields": []})
        assert result == {}
