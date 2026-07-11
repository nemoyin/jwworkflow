import json
import uuid
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.run import Run
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse, RunResponse
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("", status_code=201, response_model=WorkflowResponse)
async def create_workflow(
    body: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建工作流"""
    wf = Workflow(
        tenant_id=current_user.tenant_id,
        name=body.name,
        description=body.description,
        type=body.type,
        dag_definition=body.dag_definition,
        created_by=current_user.id,
    )
    db.add(wf)
    await db.flush()
    return WorkflowResponse(
        id=str(wf.id), name=wf.name, description=wf.description or "",
        type=wf.type, dag_definition=wf.dag_definition,
        status=wf.status, version=wf.version,
        created_at=wf.created_at.isoformat(),
    )


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流列表"""
    result = await db.execute(
        select(Workflow).where(Workflow.tenant_id == current_user.tenant_id)
    )
    workflows = result.scalars().all()
    return [
        WorkflowResponse(
            id=str(w.id), name=w.name, description=w.description or "",
            type=w.type, dag_definition=w.dag_definition,
            status=w.status, version=w.version,
            created_at=w.created_at.isoformat(),
        )
        for w in workflows
    ]


@router.get("/run/sse/{workflow_id}")
async def run_workflow_sse(
    workflow_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSE 推送：获取最近一次运行的节点执行事件"""
    wf_id = uuid.UUID(workflow_id)
    result = await db.execute(
        select(Run).where(
            Run.workflow_id == wf_id,
            Run.tenant_id == current_user.tenant_id,
        ).order_by(Run.created_at.desc()).limit(1)
    )
    run = result.scalar_one_or_none()
    if not run or not run.node_results:
        async def empty_stream():
            yield "data: {\"type\":\"no_data\"}\n\n"
        return StreamingResponse(empty_stream(), media_type="text/event-stream")

    events = run.node_results if isinstance(run.node_results, list) else []

    async def event_stream():
        for evt in events:
            if await request.is_disconnected():
                break
            event_type = evt.get("type", "node_start")
            data = json.dumps(evt.get("data", evt), ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data}\n\n"
            await asyncio.sleep(0.05)
        yield f"event: workflow_done\ndata: {json.dumps({'output': run.output}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流详情"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == uuid.UUID(workflow_id),
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return WorkflowResponse(
        id=str(wf.id), name=wf.name, description=wf.description or "",
        type=wf.type, dag_definition=wf.dag_definition,
        status=wf.status, version=wf.version,
        created_at=wf.created_at.isoformat(),
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新工作流"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == uuid.UUID(workflow_id),
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if body.name is not None:
        wf.name = body.name
    if body.description is not None:
        wf.description = body.description
    if body.dag_definition is not None:
        wf.dag_definition = body.dag_definition
    wf.version += 1
    await db.flush()
    return WorkflowResponse(
        id=str(wf.id), name=wf.name, description=wf.description or "",
        type=wf.type, dag_definition=wf.dag_definition,
        status=wf.status, version=wf.version,
        created_at=wf.created_at.isoformat(),
    )


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除工作流"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == uuid.UUID(workflow_id),
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    await db.delete(wf)
    await db.flush()


@router.post("/{workflow_id}/run", response_model=RunResponse)
async def run_workflow(
    workflow_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行工作流"""
    # 加载工作流定义
    wf_id = uuid.UUID(workflow_id)
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == wf_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 构建 DAG 并执行
    dag = WorkflowDag(
        nodes=wf.dag_definition.get("nodes", []),
        edges=wf.dag_definition.get("edges", []),
    )
    executor = WorkflowExecutor(dag, NODE_REGISTRY, db=db, tenant_id=current_user.tenant_id)

    start_time = time.time()
    try:
        output = executor.execute(body)
        duration = int((time.time() - start_time) * 1000)
        status_val = "success"
        error_text = None
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        status_val = "failed"
        output = {}
        error_text = str(e)

    # 收集节点执行结果快照
    node_results = []
    for evt in executor.get_events():
        if evt["type"] in ("node_start", "node_done", "node_error"):
            node_results.append(evt)

    # 保存运行记录
    run = Run(
        workflow_id=wf_id,
        tenant_id=current_user.tenant_id,
        triggered_by=current_user.id,
        status=status_val,
        input=body,
        output=output,
        error=error_text,
        duration_ms=duration,
        node_results=node_results,
    )
    db.add(run)
    await db.flush()

    if status_val == "failed":
        raise HTTPException(status_code=500, detail=error_text)

    return RunResponse(
        id=str(run.id),
        workflow_id=str(run.workflow_id),
        status=run.status,
        result=run.output,
        duration_ms=run.duration_ms,
        created_at=run.created_at.isoformat(),
    )
