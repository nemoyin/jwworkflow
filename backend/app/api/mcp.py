"""MCP (Model Context Protocol) 端点

支持工作流作为 MCP Server 被外部系统发现和调用。
遵循 MCP 协议规范（2025-03-26）。
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.workflow import Workflow
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/tools")
async def list_mcp_tools(
    db: AsyncSession = Depends(get_db),
):
    """MCP 协议：列出可用的工具（已发布的工作流）

    遵循 MCP ListTools 规范。
    """
    result = await db.execute(
        select(Workflow).where(Workflow.status == "published").limit(50)
    )
    workflows = result.scalars().all()

    tools = []
    for wf in workflows:
        # 提取输入参数作为工具的 inputSchema
        input_fields = []
        for node in wf.dag_definition.get("nodes", []):
            if node["type"] == "input":
                input_fields = node["config"].get("fields", [])
                break

        properties = {}
        required = []
        for field in input_fields:
            fname = field.get("name", "input")
            ftype = field.get("type", "string")
            type_map = {"text": "string", "number": "number", "file": "string", "json": "object"}
            properties[fname] = {
                "type": type_map.get(ftype, "string"),
                "description": field.get("label", fname),
            }
            required.append(fname)

        tools.append({
            "name": f"workflow_{wf.id.hex[:8]}",
            "description": wf.description or wf.name,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required if required else None,
            },
            "_workflow_id": str(wf.id),
            "_workflow_name": wf.name,
        })

    return {"tools": tools}


@router.post("/tools/{tool_name}/call")
async def call_mcp_tool(
    tool_name: str,
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """MCP 协议：调用工具（执行工作流）

    遵循 MCP CallTool 规范。
    支持 _workflow_id 直接指定工作流。
    """
    # 从 body 中提取参数
    arguments = body.get("arguments", body)
    workflow_id = arguments.pop("_workflow_id", None)

    if not workflow_id:
        # 从 tool_name 中解析 workflow_id
        result = await db.execute(
            select(Workflow).where(Workflow.status == "published").limit(50)
        )
        for wf in result.scalars().all():
            if f"workflow_{wf.id.hex[:8]}" == tool_name:
                workflow_id = str(wf.id)
                break

    if not workflow_id:
        raise HTTPException(status_code=404, detail="Tool not found")

    try:
        import uuid
        wf_id = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow ID")

    result = await db.execute(select(Workflow).where(Workflow.id == wf_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    dag = WorkflowDag(
        nodes=wf.dag_definition.get("nodes", []),
        edges=wf.dag_definition.get("edges", []),
    )
    executor = WorkflowExecutor(dag, NODE_REGISTRY)

    try:
        output = executor.execute(arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(output, ensure_ascii=False),
                }
            ],
            "isError": False,
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": str(e)}],
            "isError": True,
        }
