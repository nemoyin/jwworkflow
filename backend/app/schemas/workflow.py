from pydantic import BaseModel
from typing import Optional


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    type: str = "workflow"
    dag_definition: dict


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dag_definition: Optional[dict] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    dag_definition: dict
    status: str
    version: int
    created_at: str


class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    duration_ms: int | None = None
    created_at: str
