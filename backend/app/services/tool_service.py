"""工具市场：预置工具注册表"""

import json
from typing import Any


class BaseTool:
    name: str = ""
    description: str = ""
    parameters: dict = {}

    async def execute(self, **kwargs) -> dict:
        raise NotImplementedError


# ========== 预置工具 ==========

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "搜索互联网信息（模拟）"
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "搜索关键词"}},
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        # MVP：模拟搜索，返回模拟结果
        return {
            "results": [
                {"title": f"关于「{query}」的结果1", "url": "https://example.com/1", "snippet": f"这是关于{query}的搜索结果摘要..."},
                {"title": f"关于「{query}」的结果2", "url": "https://example.com/2", "snippet": f"更多关于{query}的信息..."},
            ],
            "total": 2,
        }


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行数学计算"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 1+2*3"}
        },
        "required": ["expression"],
    }

    async def execute(self, **kwargs) -> dict:
        expr = kwargs.get("expression", "")
        try:
            # 安全计算：只允许基本运算
            safe_globals = {"__builtins__": {}}
            safe_locals = {}
            result = eval(expr, safe_globals, safe_locals)
            return {"result": result, "expression": expr}
        except Exception as e:
            return {"error": f"计算失败: {str(e)}"}


class CurrentTimeTool(BaseTool):
    name = "current_time"
    description = "获取当前日期和时间"
    parameters = {
        "type": "object",
        "properties": {
            "format": {"type": "string", "description": "时间格式，默认 iso", "enum": ["iso", "date", "time", "timestamp"]}
        },
    }

    async def execute(self, **kwargs) -> dict:
        from datetime import datetime
        fmt = kwargs.get("format", "iso")
        now = datetime.now()
        formats = {
            "iso": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": str(now.timestamp()),
        }
        return {"now": formats.get(fmt, now.isoformat()), "format": fmt}


class WeatherTool(BaseTool):
    name = "weather"
    description = "查询天气（模拟）"
    parameters = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"],
    }

    async def execute(self, **kwargs) -> dict:
        city = kwargs.get("city", "北京")
        return {
            "city": city,
            "temperature": "22°C",
            "condition": "晴",
            "humidity": "45%",
            "wind": "3级",
        }


# ========== 注册表 ==========

BUILTIN_TOOLS: dict[str, BaseTool] = {
    tool_cls.name: tool_cls()
    for tool_cls in [WebSearchTool, CalculatorTool, CurrentTimeTool, WeatherTool]
}


def get_tool(name: str) -> BaseTool | None:
    return BUILTIN_TOOLS.get(name)


def list_tools() -> list[dict]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        }
        for tool in BUILTIN_TOOLS.values()
    ]


def get_openai_tools() -> list[dict]:
    """获取 OpenAI-compatible tool definitions"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in BUILTIN_TOOLS.values()
    ]
