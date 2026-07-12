"""DSL 导入导出 API"""

import json, uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.workflow import Workflow

router = APIRouter(prefix="/api/dsl", tags=["dsl"])


@router.get("/export/{workflow_id}")
async def export_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出工作流为 DSL JSON"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == uuid.UUID(workflow_id),
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    dsl = {
        "dsl_version": "1.0",
        "name": wf.name,
        "description": wf.description,
        "type": wf.type,
        "dag_definition": wf.dag_definition,
        "exported_at": wf.updated_at.isoformat() if wf.updated_at else wf.created_at.isoformat(),
    }
    return dsl


@router.post("/import", status_code=201)
async def import_workflow(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从 DSL JSON 导入工作流"""
    name = body.get("name", body.get("dsl_name", "导入的工作流"))
    description = body.get("description", "")
    wf_type = body.get("type", "workflow")
    dag = body.get("dag_definition", body.get("dag", {}))

    if not dag or not dag.get("nodes"):
        raise HTTPException(status_code=400, detail="DSL 中缺少 dag_definition 或 nodes")

    wf = Workflow(
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        type=wf_type,
        dag_definition=dag,
        created_by=current_user.id,
    )
    db.add(wf)
    await db.flush()

    return {"id": str(wf.id), "name": wf.name, "status": "imported"}
