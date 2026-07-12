"""工具市场 API：列出/调用预置工具"""

from fastapi import APIRouter, HTTPException
from app.services.tool_service import list_tools, get_tool

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
async def get_tools():
    """列出所有可用工具"""
    return {"tools": list_tools()}


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, body: dict = {}):
    """执行指定工具"""
    tool = get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    try:
        result = await tool.execute(**body)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
