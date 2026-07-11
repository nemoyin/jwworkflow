from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class LLMNodeExecutor(BaseNodeExecutor):
    """LLM 节点：调用大语言模型推理

    MVP 阶段为桩实现（stub），返回模拟结果。
    Phase 4 接入真实 LLM API。
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        # Stub: 返回配置中的 system_prompt 和模拟输出
        return {
            "output": f"[LLM Stub] 已收到提示词，模型: {config.get('model', 'default')}",
            "model": config.get("model", "default"),
        }
