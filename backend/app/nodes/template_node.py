from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class TemplateNodeExecutor(BaseNodeExecutor):
    """模板节点：使用 Jinja2 风格渲染变量"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        template = config.get("template", "")
        rendered = ctx.resolve_variable(template)
        return {"output": rendered}
