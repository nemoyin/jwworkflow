from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class OutputNodeExecutor(BaseNodeExecutor):
    """输出节点：从执行上下文中提取指定变量返回"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        variables = config.get("variables", [])
        result = {}
        for var in variables:
            name = var["name"]
            source = var.get("source", "")
            try:
                resolved = ctx.resolve_variable(f"{{{{ {source} }}}}")
                result[name] = resolved
            except KeyError:
                result[name] = None
        return result
