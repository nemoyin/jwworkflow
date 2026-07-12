"""LLMOps 可观测性 API"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.run import Run
from app.models.workflow import Workflow

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户级运行统计"""
    # 总运行次数
    count_result = await db.execute(
        select(func.count(Run.id)).where(Run.tenant_id == current_user.tenant_id)
    )
    total_runs = count_result.scalar() or 0

    # 成功/失败分布
    success_result = await db.execute(
        select(func.count(Run.id)).where(
            Run.tenant_id == current_user.tenant_id, Run.status == "success"
        )
    )
    success_runs = success_result.scalar() or 0
    failed_runs = total_runs - success_runs

    # 总 token 消耗
    token_result = await db.execute(
        select(func.coalesce(func.sum(Run.total_tokens), 0)).where(
            Run.tenant_id == current_user.tenant_id
        )
    )
    total_tokens = token_result.scalar() or 0

    # 平均耗时
    dur_result = await db.execute(
        select(func.coalesce(func.avg(Run.duration_ms), 0)).where(
            Run.tenant_id == current_user.tenant_id,
            Run.duration_ms.isnot(None),
        )
    )
    avg_duration = round(dur_result.scalar() or 0)

    # 工作流总数
    wf_result = await db.execute(
        select(func.count(Workflow.id)).where(Workflow.tenant_id == current_user.tenant_id)
    )
    total_workflows = wf_result.scalar() or 0

    return {
        "total_runs": total_runs,
        "success_runs": success_runs,
        "failed_runs": failed_runs,
        "success_rate": round(success_runs / total_runs * 100, 1) if total_runs > 0 else 0,
        "total_tokens": total_tokens,
        "avg_duration_ms": avg_duration,
        "total_workflows": total_workflows,
    }


@router.get("/runs/recent")
async def get_recent_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
):
    """最近运行记录（含 Token 和模型信息）"""
    result = await db.execute(
        select(Run, Workflow.name)
        .join(Workflow, Run.workflow_id == Workflow.id, isouter=True)
        .where(Run.tenant_id == current_user.tenant_id)
        .order_by(Run.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": str(run.id),
            "workflow_id": str(run.workflow_id),
            "workflow_name": wf_name or "",
            "status": run.status,
            "duration_ms": run.duration_ms,
            "total_tokens": run.total_tokens or 0,
            "model_used": run.model_used or "",
            "created_at": run.created_at.isoformat() if run.created_at else "",
        }
        for run, wf_name in rows
    ]
