"""Webhook 触发 API：通过 HTTP 请求触发工作流"""

import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.workflow import Workflow
from app.models.run import Run
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/trigger/{workflow_id}")
async def trigger_webhook(
    workflow_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """通过 Webhook 触发工作流执行（无需认证）"""
    try:
        wf_id = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow ID")

    result = await db.execute(select(Workflow).where(Workflow.id == wf_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 获取请求体
    try:
        body = await request.json()
    except Exception:
        body = {}

    # 包装 webhook 数据
    inputs = {"_webhook_data": {
        "body": body,
        "headers": dict(request.headers),
        "method": request.method,
    }}

    # 构建 DAG 并执行
    dag = WorkflowDag(
        nodes=wf.dag_definition.get("nodes", []),
        edges=wf.dag_definition.get("edges", []),
    )
    executor = WorkflowExecutor(dag, NODE_REGISTRY)

    start_time = time.time()
    try:
        output = executor.execute(inputs)
        duration = int((time.time() - start_time) * 1000)
        status_val = "success"
        error_text = None
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        status_val = "failed"
        output = {}
        error_text = str(e)

    node_results = []
    for evt in executor.get_events():
        if evt["type"] in ("node_start", "node_done", "node_error"):
            node_results.append(evt)

    run = Run(
        workflow_id=wf_id,
        tenant_id=wf.tenant_id,
        status=status_val,
        input=inputs,
        output=output,
        error=error_text,
        duration_ms=duration,
        node_results=node_results,
    )
    db.add(run)
    await db.commit()

    if status_val == "failed":
        raise HTTPException(status_code=500, detail=error_text)

    return {"status": "success", "output": output, "run_id": str(run.id)}
