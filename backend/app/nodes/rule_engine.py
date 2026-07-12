"""规则引擎节点：确定性业务规则判定"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class RuleEngineNodeExecutor(BaseNodeExecutor):
    """规则引擎节点：基于配置的规则对输入数据进行判定

    支持规则类型:
    - eq / ne: 等于/不等于
    - gt / gte / lt / lte: 数值比较
    - contains: 包含
    - between: 数值在区间内
    - count_distinct_lt / count_distinct_gte: 去重计数比较
    - deviation_gt / deviation_lte: 偏离百分比
    - regex_match: 正则匹配
    - is_empty / is_not_empty: 空值判断

    组合方式:
    - any: 任一规则命中即触发
    - all: 全部规则命中才触发
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        rules = config.get("rules", [])
        combine = config.get("combine", "any")
        results = []
        triggered = 0

        for rule in rules:
            result = self._evaluate_rule(rule, ctx)
            results.append(result)
            if result["matched"]:
                triggered += 1

        is_triggered = (triggered > 0) if combine == "any" else (triggered == len(rules))

        return {
            "triggered": is_triggered,
            "triggered_count": triggered,
            "total_rules": len(rules),
            "combine": combine,
            "results": results,
            "severity": self._get_max_severity(results) if results else "none",
        }

    @staticmethod
    def _evaluate_rule(rule: dict, ctx: ExecutionContext) -> dict:
        name = rule.get("name", "unknown")
        field = rule.get("field", "")
        operator = rule.get("operator", "eq")
        threshold = rule.get("threshold")
        severity = rule.get("severity", "medium")

        # 解析字段值
        raw_value = field
        if "{{" in str(field):
            try:
                raw_value = ctx.resolve_variable(field)
            except KeyError:
                raw_value = None
        else:
            raw_value = ctx.inputs.get(field) if field in ctx.inputs else None

        matched = False
        detail = ""

        try:
            if operator == "eq":
                matched = raw_value == threshold
                detail = f"{raw_value} == {threshold}"
            elif operator == "ne":
                matched = raw_value != threshold
                detail = f"{raw_value} != {threshold}"
            elif operator == "gt":
                matched = float(raw_value) > float(threshold)
                detail = f"{raw_value} > {threshold}"
            elif operator == "gte":
                matched = float(raw_value) >= float(threshold)
                detail = f"{raw_value} >= {threshold}"
            elif operator == "lt":
                matched = float(raw_value) < float(threshold)
                detail = f"{raw_value} < {threshold}"
            elif operator == "lte":
                matched = float(raw_value) <= float(threshold)
                detail = f"{raw_value} <= {threshold}"
            elif operator == "contains":
                matched = str(threshold) in str(raw_value)
                detail = f"'{threshold}' in '{raw_value}'"
            elif operator == "between":
                lo, hi = threshold[0], threshold[1]
                matched = lo <= float(raw_value) <= hi
                detail = f"{raw_value} in [{lo}, {hi}]"
            elif operator == "count_distinct_lt":
                count = len(set(raw_value)) if isinstance(raw_value, (list, set)) else 0
                matched = count < int(threshold)
                detail = f"distinct count {count} < {threshold}"
            elif operator == "count_distinct_gte":
                count = len(set(raw_value)) if isinstance(raw_value, (list, set)) else 0
                matched = count >= int(threshold)
                detail = f"distinct count {count} >= {threshold}"
            elif operator == "deviation_gt":
                val = float(raw_value)
                ref = float(threshold)
                dev = abs(val - ref) / ref if ref != 0 else float("inf")
                matched = dev > rule.get("deviation_ratio", 0.2)
                detail = f"deviation {dev:.2%} > {rule.get('deviation_ratio', 0.2):.0%}"
            elif operator == "regex_match":
                import re
                matched = bool(re.search(str(threshold), str(raw_value)))
                detail = f"regex /{threshold}/ matches '{raw_value}'"
            elif operator == "is_empty":
                matched = raw_value is None or raw_value == "" or raw_value == []
                detail = f"'{raw_value}' is empty"
            elif operator == "is_not_empty":
                matched = raw_value is not None and raw_value != "" and raw_value != []
                detail = f"'{raw_value}' is not empty"
        except (TypeError, ValueError, ZeroDivisionError) as e:
            detail = f"eval error: {e}"

        return {"name": name, "field": field, "operator": operator,
                "matched": matched, "severity": severity, "detail": detail}

    @staticmethod
    def _get_max_severity(results: list) -> str:
        levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_sev = max(results, key=lambda r: levels.get(r.get("severity", "low"), 0))
        return max_sev.get("severity", "medium")
