from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class InputNodeExecutor(BaseNodeExecutor):
    """输入节点：从工作流输入中提取字段"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        fields = config.get("fields", [])
        result = {}
        for field in fields:
            name = field["name"]
            if name in ctx.inputs:
                result[name] = ctx.inputs[name]
        return result
