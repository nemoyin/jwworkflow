"""规则引擎节点测试"""

import pytest
from app.engine.context import ExecutionContext
from app.nodes.rule_engine import RuleEngineNodeExecutor


class TestRuleEngine:
    def test_gt_triggered(self):
        ctx = ExecutionContext({"score": 85})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "高分", "field": "score", "operator": "gt", "threshold": 80, "severity": "high"}],
            "combine": "any",
        })
        assert result["triggered"] is True
        assert result["triggered_count"] == 1
        assert result["results"][0]["matched"] is True

    def test_gt_not_triggered(self):
        ctx = ExecutionContext({"score": 75})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "高分", "field": "score", "operator": "gt", "threshold": 80}],
        })
        assert result["triggered"] is False

    def test_combine_all(self):
        ctx = ExecutionContext({"a": 10, "b": 20})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [
                {"name": "R1", "field": "a", "operator": "gt", "threshold": 5},
                {"name": "R2", "field": "b", "operator": "lt", "threshold": 30},
            ],
            "combine": "all",
        })
        assert result["triggered"] is True

    def test_combine_all_partial(self):
        ctx = ExecutionContext({"a": 1, "b": 20})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [
                {"name": "R1", "field": "a", "operator": "gt", "threshold": 5},
                {"name": "R2", "field": "b", "operator": "lt", "threshold": 30},
            ],
            "combine": "all",
        })
        assert result["triggered"] is False

    def test_contains(self):
        ctx = ExecutionContext({"text": "hello world"})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "含hello", "field": "text", "operator": "contains", "threshold": "hello"}],
        })
        assert result["results"][0]["matched"] is True

    def test_between(self):
        ctx = ExecutionContext({"price": 50})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "价格区间", "field": "price", "operator": "between", "threshold": [30, 70]}],
        })
        assert result["results"][0]["matched"] is True

    def test_regex(self):
        ctx = ExecutionContext({"email": "test@example.com"})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "邮箱格式", "field": "email", "operator": "regex_match", "threshold": r"^[\w.]+@\w+\.\w+$"}],
        })
        assert result["results"][0]["matched"] is True

    def test_count_distinct(self):
        ctx = ExecutionContext({"ips": ["1.1.1.1", "1.1.1.1", "2.2.2.2"]})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "IP去重", "field": "ips", "operator": "count_distinct_lt", "threshold": 3}],
        })
        assert result["results"][0]["matched"] is True

    def test_deviation(self):
        ctx = ExecutionContext({"price": 120})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "偏离", "field": "price", "operator": "deviation_gt",
                       "threshold": 100, "deviation_ratio": 0.15}],
        })
        assert result["results"][0]["matched"] is True

    def test_empty_rules(self):
        ctx = ExecutionContext({"x": 1})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {"rules": []})
        assert result["triggered"] is False
        assert result["total_rules"] == 0

    def test_severity_propagation(self):
        ctx = ExecutionContext({"score": 95})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "严重", "field": "score", "operator": "gt", "threshold": 90, "severity": "critical"}],
        })
        assert result["severity"] == "critical"

    def test_is_empty(self):
        ctx = ExecutionContext({"name": ""})
        executor = RuleEngineNodeExecutor()
        result = executor.execute(ctx, {
            "rules": [{"name": "空", "field": "name", "operator": "is_empty", "threshold": None}],
        })
        assert result["results"][0]["matched"] is True
