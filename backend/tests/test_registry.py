import pytest
from app.nodes.base import BaseNodeExecutor
from app.nodes.registry import register_node, get_node


class TestNodeRegistry:
    def test_register_and_get(self):
        """验证注册和获取节点执行器"""
        registry = {}

        class TestNode(BaseNodeExecutor):
            def execute(self, ctx, config):
                return {"result": "test"}

        register_node(registry, "test", TestNode)
        cls = get_node(registry, "test")
        assert cls is TestNode

    def test_get_nonexistent(self):
        """验证获取不存在的节点返回 None"""
        assert get_node({}, "nonexistent") is None
