"""Answer 节点：Chatflow 流式输出"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class AnswerNodeExecutor(BaseNodeExecutor):
    """Answer 节点：Chatflow 的输出节点，支持流式 Markdown 响应

    在 Chatflow 中作为终止节点，将上游输出格式化为对话响应。
    支持:
    - 文本输出
    - Markdown 渲染
    - 引用来源标记
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        source = config.get("source", "")
        content = ""

        if source:
            try:
                content = ctx.resolve_variable(f"{{{{ {source} }}}}")
            except KeyError:
                content = f"[Error] 无法解析来源: {source}"
        else:
            # 没有配置 source 时尝试从上下文获取上一个节点的输出
            for node_id in reversed(list(ctx._outputs.keys())):
                output = ctx._outputs[node_id]
                if isinstance(output, dict):
                    content = str(output.get("output", output.get("text", str(output))))
                    break

        if not isinstance(content, str):
            content = str(content)

        return {
            "content": content,
            "type": config.get("output_type", "markdown"),
            "show_references": config.get("show_references", False),
        }
