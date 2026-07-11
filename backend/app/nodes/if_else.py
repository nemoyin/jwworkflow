"""If-Else condition branching node.

Evaluates a list of conditions in order and returns the first matching branch.
If no condition matches, returns the default branch.
"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class IfElseNodeExecutor(BaseNodeExecutor):
    """条件分支节点：根据条件表达式选择执行路径"""

    # Supported comparison operators
    OPERATORS = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "gt": lambda a, b: float(a) > float(b),
        "gte": lambda a, b: float(a) >= float(b),
        "lt": lambda a, b: float(a) < float(b),
        "lte": lambda a, b: float(a) <= float(b),
        "contains": lambda a, b: b in str(a) if b is not None else False,
        "is_empty": lambda a, _: not a,
    }

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        conditions = config.get("conditions", [])

        for cond in conditions:
            variable = cond.get("variable", "")
            operator = cond.get("operator", "eq")
            value = cond.get("value")

            # Resolve variable if it contains template syntax
            if "{{" in str(variable):
                resolved = ctx.resolve_variable(variable)
            else:
                resolved = variable

            # Evaluate condition
            op_func = self.OPERATORS.get(operator)
            if op_func is None:
                result = False
            else:
                try:
                    result = op_func(resolved, value)
                except (ValueError, TypeError):
                    result = False

            if result:
                return {
                    "selected_branch": cond.get("branch", "default"),
                    "matched": True,
                }

        return {"selected_branch": "default", "matched": False}
