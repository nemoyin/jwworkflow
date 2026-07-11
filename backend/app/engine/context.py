import re
from functools import reduce


class ExecutionContext:
    """工作流执行上下文，管理节点间变量传递"""

    VARIABLE_PATTERN = re.compile(r"\{\{\s*([^}]+)\s*\}\}")

    def __init__(self, inputs: dict):
        self._inputs = inputs
        self._outputs: dict[str, dict] = {}

    @property
    def inputs(self) -> dict:
        return self._inputs

    def set(self, node_id: str, output: dict):
        """存储节点输出"""
        self._outputs[node_id] = output

    def get(self, node_id: str) -> dict:
        """获取节点输出"""
        if node_id not in self._outputs:
            raise KeyError(f"Node {node_id} has no output yet")
        return self._outputs[node_id]

    def resolve_variable(self, expression: str) -> any:
        """解析变量引用表达式

        支持格式:
        - {{ n1.field.subfield }}
        - {{ input.var_name }}
        - 纯文本 (无变量, 原样返回)
        """
        match = self.VARIABLE_PATTERN.search(expression)
        if not match:
            return expression

        path = match.group(1).strip().split(".")
        source = path[0]

        if source == "input":
            value = self._inputs
        else:
            if source not in self._outputs:
                raise KeyError(f"Cannot resolve '{expression}': node '{source}' has no output")
            value = self._outputs[source]

        # 按路径逐层访问
        for key in path[1:]:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                raise KeyError(f"Cannot resolve '{expression}': '{key}' not found")
            if value is None:
                raise KeyError(f"Cannot resolve '{expression}': '{key}' is None")

        return value
