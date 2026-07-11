"""Human Input Node — placeholder for manual review / human-in-the-loop.

Actual frontend integration (showing a prompt to the user and collecting
input) depends on the SSE event stream and frontend implementation.
This node returns a status indicating that human approval is needed.
"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class HumanInputNodeExecutor(BaseNodeExecutor):
    """人工输入节点：等待人工审核/输入的占位节点

    Config
    ------
    prompt : str, optional
        向用户展示的提示文字（默认：``"Please review and provide input"``）
    fields : list[dict], optional
        需要用户填写的字段列表（每个字段有 ``name`` 和 ``type``）
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        return {
            "status": "waiting_for_input",
            "prompt": config.get("prompt", "Please review and provide input"),
            "fields": config.get("fields", []),
            "approval_required": True,
        }
