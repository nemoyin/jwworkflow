import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.run import Run
from app.models.workflow import Workflow

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunListItem(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    status: str
    triggered_by: Optional[str] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: str


class RunDetail(RunListItem):
    input: dict = {}
    output: dict = {}
    node_results: Optional[list] = None


@router.get("", response_model=list[RunListItem])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前租户的运行历史列表"""
    result = await db.execute(
        select(Run, Workflow.name)
        .join(Workflow, Run.workflow_id == Workflow.id)
        .where(Run.tenant_id == current_user.tenant_id)
        .order_by(Run.created_at.desc())
    )
    rows = result.all()
    return [
        RunListItem(
            id=str(run.id),
            workflow_id=str(run.workflow_id),
            workflow_name=workflow_name,
            status=run.status,
            triggered_by=str(run.triggered_by) if run.triggered_by else None,
            duration_ms=run.duration_ms,
            error=run.error,
            created_at=run.created_at.isoformat(),
        )
        for run, workflow_name in rows
    ]


@router.get("/{run_id}", response_model=RunDetail)
async def get_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取运行详情"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的运行 ID")

    result = await db.execute(
        select(Run, Workflow.name)
        .join(Workflow, Run.workflow_id == Workflow.id)
        .where(Run.id == run_uuid, Run.tenant_id == current_user.tenant_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    run, workflow_name = row
    return RunDetail(
        id=str(run.id),
        workflow_id=str(run.workflow_id),
        workflow_name=workflow_name,
        status=run.status,
        triggered_by=str(run.triggered_by) if run.triggered_by else None,
        input=run.input or {},
        output=run.output or {},
        error=run.error,
        duration_ms=run.duration_ms,
        node_results=run.node_results,
        created_at=run.created_at.isoformat(),
    )
