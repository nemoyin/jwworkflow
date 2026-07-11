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

        将字符串中所有 {{ ... }} 模式替换为对应的变量值。
        若整个字符串就是一个变量引用，返回原始值（保持类型不变）；
        否则返回渲染后的字符串。

        支持格式:
        - {{ n1.field.subfield }}
        - {{ input.var_name }}
        - 纯文本 (无变量, 原样返回)
        - "Result: {{ n1.field }}, {{ input.var }}" (渲染模板)
        """
        matches = list(self.VARIABLE_PATTERN.finditer(expression))

        # 整个字符串正好是一个变量引用 -> 返回原始值 (保持类型)
        if len(matches) == 1:
            start, end = matches[0].start(), matches[0].end()
            if expression.strip() == expression[start:end]:
                path = matches[0].group(1).strip().split(".")
                return self._resolve_path(expression, path)

        # 多变量 / 混合文本 -> 渲染为字符串
        if matches:
            return self._render_template(expression, matches)

        return expression

    def _resolve_path(self, expression: str, path: list[str]) -> any:
        """根据路径从上下文取值"""
        source = path[0]

        if source == "input":
            value = self._inputs
        else:
            if source not in self._outputs:
                raise KeyError(f"Cannot resolve '{expression}': node '{source}' has no output")
            value = self._outputs[source]

        for key in path[1:]:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                raise KeyError(f"Cannot resolve '{expression}': '{key}' not found")
            if value is None:
                raise KeyError(f"Cannot resolve '{expression}': '{key}' is None")

        return value

    def _render_template(self, expression: str, matches: list[re.Match]) -> str:
        """将模板字符串中的所有变量替换为字符串值"""

        def _replacer(match):
            path = match.group(1).strip().split(".")
            value = self._resolve_path(expression, path)
            return str(value)

        return self.VARIABLE_PATTERN.sub(_replacer, expression)
