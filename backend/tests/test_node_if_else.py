"""Tests for IfElseNodeExecutor — condition evaluation and branch selection."""

import pytest
from app.engine.context import ExecutionContext
from app.nodes.if_else import IfElseNodeExecutor


class TestIfElseNode:
    def test_eq_condition_matches(self):
        """验证 eq 操作符匹配时返回对应分支"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"status": "active"})
        config = {
            "conditions": [
                {"variable": "{{ input.status }}", "operator": "eq", "value": "active", "branch": "active_branch"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"selected_branch": "active_branch", "matched": True}

    def test_eq_condition_not_matches(self):
        """验证 eq 操作符不匹配时走默认分支"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"status": "inactive"})
        config = {
            "conditions": [
                {"variable": "{{ input.status }}", "operator": "eq", "value": "active", "branch": "active_branch"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"selected_branch": "default", "matched": False}

    def test_multiple_conditions_first_match_wins(self):
        """验证多条件中第一个匹配的生效"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"score": 85})
        config = {
            "conditions": [
                {"variable": "{{ input.score }}", "operator": "gte", "value": 90, "branch": "excellent"},
                {"variable": "{{ input.score }}", "operator": "gte", "value": 80, "branch": "good"},
                {"variable": "{{ input.score }}", "operator": "gte", "value": 60, "branch": "pass"},
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"selected_branch": "good", "matched": True}

    def test_ne_operator(self):
        """验证 ne（不等）操作符"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"role": "admin"})
        config = {
            "conditions": [
                {"variable": "{{ input.role }}", "operator": "ne", "value": "guest", "branch": "authenticated"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "authenticated"

    def test_gt_operator(self):
        """验证 gt（大于）操作符"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"age": 25})
        config = {
            "conditions": [
                {"variable": "{{ input.age }}", "operator": "gt", "value": 18, "branch": "adult"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "adult"

    def test_gte_operator_boundary(self):
        """验证 gte（大于等于）边界值"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"age": 18})
        config = {
            "conditions": [
                {"variable": "{{ input.age }}", "operator": "gte", "value": 18, "branch": "adult"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "adult"

    def test_lt_operator(self):
        """验证 lt（小于）操作符"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"price": 50})
        config = {
            "conditions": [
                {"variable": "{{ input.price }}", "operator": "lt", "value": 100, "branch": "cheap"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "cheap"

    def test_lte_operator_boundary(self):
        """验证 lte（小于等于）边界值"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"price": 100})
        config = {
            "conditions": [
                {"variable": "{{ input.price }}", "operator": "lte", "value": 100, "branch": "affordable"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "affordable"

    def test_contains_operator(self):
        """验证 contains（包含）操作符"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"email": "user@example.com"})
        config = {
            "conditions": [
                {"variable": "{{ input.email }}", "operator": "contains", "value": "@", "branch": "valid_email"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "valid_email"

    def test_is_empty_operator_true(self):
        """验证 is_empty 对空值返回 True"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"comment": ""})
        config = {
            "conditions": [
                {"variable": "{{ input.comment }}", "operator": "is_empty", "value": None, "branch": "no_comment"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "no_comment"

    def test_is_empty_operator_false(self):
        """验证 is_empty 对非空值返回 False"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"comment": "hello"})
        config = {
            "conditions": [
                {"variable": "{{ input.comment }}", "operator": "is_empty", "value": None, "branch": "no_comment"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "default"

    def test_unknown_operator_returns_default(self):
        """验证未知操作符返回默认分支"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"x": 1})
        config = {
            "conditions": [
                {"variable": "{{ input.x }}", "operator": "unknown_op", "value": 1, "branch": "matched"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result == {"selected_branch": "default", "matched": False}

    def test_no_conditions_returns_default(self):
        """验证无条件时返回默认分支"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({})
        config = {"conditions": []}
        result = executor.execute(ctx, config)
        assert result == {"selected_branch": "default", "matched": False}

    def test_direct_variable_without_template_syntax(self):
        """验证非模板表达式变量原样使用"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"x": 42})
        config = {
            "conditions": [
                {"variable": "direct_value", "operator": "eq", "value": "direct_value", "branch": "same"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "same"

    def test_compare_node_output(self):
        """验证比较来自其他节点的输出"""
        executor = IfElseNodeExecutor()
        ctx = ExecutionContext({"threshold": 3})
        ctx.set("n1", {"count": 5})
        config = {
            "conditions": [
                {"variable": "{{ n1.count }}", "operator": "gt", "value": 3, "branch": "above_threshold"}
            ]
        }
        result = executor.execute(ctx, config)
        assert result["selected_branch"] == "above_threshold"
