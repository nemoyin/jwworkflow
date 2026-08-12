"""工作流流式执行端点：SSE 实时推送节点执行进度。"""

import json
import time
import uuid
import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor


def _safe_json(obj) -> str:
    """安全 JSON 序列化：NaN/Infinity → null。"""
    return json.dumps(obj, ensure_ascii=False, default=str)


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.run import Run
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY

router = APIRouter(prefix="/api/workflows", tags=["workflow-stream"])

_executor_pool = ThreadPoolExecutor(max_workers=4)


def _put_in_queue(loop: asyncio.AbstractEventLoop, queue: asyncio.Queue, item):
    """线程安全地向 asyncio.Queue 放入一个事件。"""
    loop.call_soon_threadsafe(queue.put_nowait, item)


@router.post("/{workflow_id}/run-stream")
async def run_workflow_stream(
    workflow_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """流式执行工作流，SSE 实时推送每个节点的执行状态。"""
    try:
        wf_id = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的 workflow ID")

    result = await db.execute(
        select(Workflow).where(
            Workflow.id == wf_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    dag = WorkflowDag(
        nodes=wf.dag_definition.get("nodes", []),
        edges=wf.dag_definition.get("edges", []),
    )
    executor = WorkflowExecutor(dag, NODE_REGISTRY, db=db, tenant_id=current_user.tenant_id)

    event_queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    start_time = time.time()
    step_events: list[dict] = []

    def progress_callback(evt: dict):
        """在同步线程中被调用，通过 call_soon_threadsafe 安全入队。"""
        _put_in_queue(loop, event_queue, evt)

    def run_in_thread():
        """在线程中同步执行工作流。"""
        try:
            output = executor.execute(body, progress_callback=progress_callback)
            _put_in_queue(loop, event_queue, {"type": "_executor_done", "output": output or {}})
        except Exception as e:
            _put_in_queue(loop, event_queue, {
                "type": "_executor_error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })

    loop.run_in_executor(_executor_pool, run_in_thread)

    async def event_generator():
        nonlocal step_events
        last_heartbeat = time.time()

        while True:
            try:
                evt = await asyncio.wait_for(event_queue.get(), timeout=15)
                last_heartbeat = time.time()
            except asyncio.TimeoutError:
                # 15 秒无事件 → 心跳保活
                yield "event: heartbeat\ndata: {}\n\n"
                # 如果超过 120 秒无结果，主动终止
                if time.time() - start_time > 120:
                    yield "event: workflow_error\ndata: {}\n\n"
                    break
                continue

            evt_type = evt.get("type", "")

            if evt_type == "_executor_done":
                output = evt.get("output", {})
                duration = int((time.time() - start_time) * 1000)

                # 保存运行记录到数据库
                run_record = Run(
                    workflow_id=wf_id,
                    tenant_id=current_user.tenant_id,
                    triggered_by=current_user.id,
                    status="success",
                    input=body,
                    output=output,
                    duration_ms=duration,
                    node_results=step_events,
                )
                db.add(run_record)
                await db.flush()

                yield (
                    f"event: workflow_done\n"
                    f"data: {_safe_json({'output': output, 'duration_ms': duration, 'run_id': str(run_record.id)})}\n\n"
                )
                break

            elif evt_type == "_executor_error":
                error_text = evt.get("error", "未知错误")
                duration = int((time.time() - start_time) * 1000)

                run_record = Run(
                    workflow_id=wf_id,
                    tenant_id=current_user.tenant_id,
                    triggered_by=current_user.id,
                    status="failed",
                    input=body,
                    output={},
                    error=error_text,
                    duration_ms=duration,
                    node_results=step_events,
                )
                db.add(run_record)
                await db.flush()

                yield (
                    f"event: workflow_error\n"
                    f"data: {_safe_json({'error': error_text, 'traceback': evt.get('traceback', ''), 'duration_ms': duration})}\n\n"
                )
                break

            else:
                # 常规事件，转发给前端作为 SSE
                # 注意: workflow_done 和 workflow_start 由 executor 产生，
                # 但真正的 workflow_done/start 由 _executor_done 处理，
                # 这里跳过避免前端收到重复事件
                if evt_type in ("workflow_done", "workflow_start"):
                    # 仍记录到 step_events 用于持久化，但不转发给前端
                    step_events.append(evt)
                    continue
                step_events.append(evt)
                yield f"event: {evt_type}\ndata: {_safe_json(evt)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
