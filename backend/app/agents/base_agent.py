"""BaseScenarioAgent — abstract base class for scenario-specific AI agents."""

from abc import ABC, abstractmethod

from app.schemas.tool import ToolDefinition


class BaseScenarioAgent(ABC):
    """场景智能体基类

    所有场景智能体必须继承此类并实现以下抽象成员：

    - :attr:`name` — 智能体名称
    - :attr:`description` — 智能体用途描述
    - :meth:`execute` — 执行智能体逻辑

    通过 :meth:`to_tool_definition` 可将智能体包装为 Agent 节点的工具定义，
    实现与 Agent 工作流节点的无缝集成。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """智能体名称（用于 Agent 节点的工具选择）。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """智能体用途描述（用于 LLM 理解工具用途）。"""
        ...

    @abstractmethod
    async def execute(self, params: dict) -> dict:
        """执行智能体逻辑

        Parameters
        ----------
        params : dict
            智能体输入参数。

        Returns
        -------
        dict
            智能体执行结果。
        """
        ...

    # ------------------------------------------------------------------
    # Tool integration
    # ------------------------------------------------------------------

    def to_tool_definition(self) -> ToolDefinition:
        """将当前智能体包装为 Agent 节点的工具定义。

        生成的工具定义将智能体注册为一个 HTTP 工具，其 endpoint
        指向 ``/api/v1/agents/{name}``。Agent 节点通过该 endpoint
        调用智能体的 :meth:`execute` 逻辑。

        Returns
        -------
        ToolDefinition
            可在 Agent 节点配置中使用的工具定义。
        """
        return ToolDefinition(
            name=self.name,
            description=self.description,
            endpoint=f"http://localhost:8000/api/v1/agents/{self.name}",
            method="POST",
            input_schema=self._input_schema(),
        )

    def _input_schema(self) -> dict:
        """返回输入参数的 JSON Schema 描述。

        子类可重写此方法以提供更精确的参数描述。

        Returns
        -------
        dict
            符合 JSON Schema 规范的参数描述。
        """
        return {
            "type": "object",
            "properties": {},
            "description": f"Input parameters for {self.name} agent.",
        }


__all__ = ["BaseScenarioAgent"]
