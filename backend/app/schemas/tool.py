"""Tool definition schema for Agent node."""

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """工具定义模式

    Attributes
    ----------
    name : str
        工具名称，供 LLM 引用
    description : str
        工具描述，供 LLM 理解用途
    endpoint : str
        工具执行入口：
        - URL（如 ``https://api.example.com/search``）→ 发起 HTTP 请求
        - ``"code"`` → 执行 input_schema 中 ``code`` 字段定义的 Python 沙箱代码
    method : str
        HTTP 方法（仅 endpoint 为 URL 时有效，默认 ``"GET"``）
    input_schema : dict
        输入参数 schema 描述。当 endpoint 为 ``"code"`` 时，须包含 ``code`` 键。
    """

    name: str
    description: str
    endpoint: str  # URL or "code"
    method: str = "GET"
    input_schema: dict = {}
