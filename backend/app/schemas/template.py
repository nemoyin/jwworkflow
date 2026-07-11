from pydantic import BaseModel
from typing import Optional


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    dag_definition: dict
    icon: str
    sort_order: int
    is_builtin: bool
    created_at: str


class TemplateInstantiateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TemplateInstantiateResponse(BaseModel):
    workflow_id: str
    workflow_name: str
