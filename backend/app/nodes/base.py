from abc import ABC, abstractmethod

from app.engine.context import ExecutionContext


class BaseNodeExecutor(ABC):
    """所有节点执行器的抽象基类"""

    @abstractmethod
    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        """执行节点逻辑

        Args:
            ctx: 执行上下文
            config: 节点配置

        Returns:
            节点输出字典
        """
        pass
