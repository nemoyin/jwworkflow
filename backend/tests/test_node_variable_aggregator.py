"""Tests for VariableAggregatorNode — merging outputs from multiple branches."""

import pytest
from app.engine.context import ExecutionContext
from app.nodes.variable_aggregator import VariableAggregatorNode


class TestVariableAggregator:
    def test_merge_multiple_sources(self):
        """验证合并多个源节点输出"""
        executor = VariableAggregatorNode()
        ctx = ExecutionContext({})
        ctx.set("n1", {"result": "from_branch_a"})
        ctx.set("n2", {"result": "from_branch_b"})
        config = {
            "sources": [
                {"node_id": "n1", "alias": "branch_a"},
                {"node_id": "n2", "alias": "branch_b"},
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {
            "branch_a": {"result": "from_branch_a"},
            "branch_b": {"result": "from_branch_b"},
        }

    def test_single_source(self):
        """验证单个源"""
        executor = VariableAggregatorNode()
        ctx = ExecutionContext({})
        ctx.set("n1", {"value": 42})
        config = {
            "sources": [
                {"node_id": "n1", "alias": "output"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"output": {"value": 42}}

    def test_empty_sources(self):
        """验证无源时返回空字典"""
        executor = VariableAggregatorNode()
        ctx = ExecutionContext({})
        config = {"sources": []}
        result = executor.execute(ctx, config)
        assert result == {}

    def test_merged_output_flat_mode(self):
        """验证 flat 模式将各源字段平铺"""
        executor = VariableAggregatorNode()
        ctx = ExecutionContext({})
        ctx.set("n1", {"text": "hello", "score": 0.9})
        ctx.set("n2", {"text": "world"})
        config = {
            "sources": [
                {"node_id": "n1", "alias": "a"},
                {"node_id": "n2", "alias": "b"},
            ],
            "mode": "flat"
        }
        result = executor.execute(ctx, config)
        assert result["a"] == {"text": "hello", "score": 0.9}
        assert result["b"] == {"text": "world"}

    def test_nonexistent_source_node(self):
        """验证不存在的源节点返回空字典作为其输出"""
        executor = VariableAggregatorNode()
        ctx = ExecutionContext({})
        config = {
            "sources": [
                {"node_id": "nonexistent", "alias": "missing"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"missing": None}

    def test_multiple_fields_in_source(self):
        """验证源节点输出含多个字段"""
        executor = VariableAggregatorNode()
        ctx = ExecutionContext({})
        ctx.set("n1", {"a": 1, "b": 2, "c": 3})
        config = {
            "sources": [
                {"node_id": "n1", "alias": "data"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"data": {"a": 1, "b": 2, "c": 3}}
