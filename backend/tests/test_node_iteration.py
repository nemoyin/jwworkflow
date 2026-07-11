"""Tests for IterationNodeExecutor — array iteration and sub-item execution."""

import pytest
from app.engine.context import ExecutionContext
from app.nodes.iteration import IterationNodeExecutor


class TestIterationNode:
    def test_iterate_over_input_array(self):
        """验证迭代输入数组"""
        executor = IterationNodeExecutor()
        ctx = ExecutionContext({"items": ["a", "b", "c"]})
        config = {
            "items_source": "{{ input.items }}",
            "item_variable": "current_item",
            "sub_nodes": [
                {"type": "template", "config": {"template": "Item: {{ input.current_item }}"}}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["iteration_count"] == 3
        assert len(result["results"]) == 3
        assert result["results"][0]["output"] == "Item: a"

    def test_iterate_over_node_output_array(self):
        """验证迭代来自其他节点输出的数组"""
        executor = IterationNodeExecutor()
        ctx = ExecutionContext({})
        ctx.set("n1", {"values": [10, 20, 30]})
        config = {
            "items_source": "{{ n1.values }}",
            "item_variable": "val",
            "sub_nodes": []
        }
        result = executor.execute(ctx, config)
        assert result["iteration_count"] == 3
        assert result["results"] == [10, 20, 30]

    def test_empty_array(self):
        """验证空数组迭代返回零结果"""
        executor = IterationNodeExecutor()
        ctx = ExecutionContext({"items": []})
        config = {
            "items_source": "{{ input.items }}",
            "item_variable": "current_item",
            "sub_nodes": []
        }
        result = executor.execute(ctx, config)
        assert result["iteration_count"] == 0
        assert result["results"] == []

    def test_non_array_source_raises_error(self):
        """验证非数组源抛出异常"""
        executor = IterationNodeExecutor()
        ctx = ExecutionContext({"items": "not_an_array"})
        config = {
            "items_source": "{{ input.items }}",
            "item_variable": "current_item",
            "sub_nodes": []
        }
        with pytest.raises(TypeError, match="must be a list"):
            executor.execute(ctx, config)

    def test_array_from_another_node(self):
        """验证从其他节点输出中获取数组"""
        executor = IterationNodeExecutor()
        ctx = ExecutionContext({})
        ctx.set("data_node", {"list": [{"id": 1}, {"id": 2}]})
        config = {
            "items_source": "{{ data_node.list }}",
            "item_variable": "item",
            "sub_nodes": []
        }
        result = executor.execute(ctx, config)
        assert result["iteration_count"] == 2
        assert result["results"] == [{"id": 1}, {"id": 2}]

    def test_sub_node_template_execution(self):
        """验证子节点模板执行"""
        executor = IterationNodeExecutor()
        ctx = ExecutionContext({"names": ["Alice", "Bob"]})
        config = {
            "items_source": "{{ input.names }}",
            "item_variable": "name",
            "sub_nodes": [
                {"type": "template", "config": {"template": "Hello {{ input.name }}!"}}
            ]
        }
        result = executor.execute(ctx, config)
        assert len(result["results"]) == 2
        assert result["results"][0]["output"] == "Hello Alice!"
        assert result["results"][1]["output"] == "Hello Bob!"
