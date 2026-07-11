"""多模型管理 Pydantic Schemas"""

from pydantic import BaseModel
from typing import Optional


class ProviderCreate(BaseModel):
    name: str
    provider_type: str = "openai"
    api_key: str = ""
    base_url: str = ""
    is_active: bool = True
    sort_order: int = 0


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    api_key: str
    base_url: str
    is_active: bool
    sort_order: int
    created_at: str
    model_count: int = 0


class ModelCreate(BaseModel):
    provider_id: str
    model_name: str
    display_name: str = ""
    capabilities: dict = {}
    is_active: bool = True
    sort_order: int = 0


class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    capabilities: Optional[dict] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ModelResponse(BaseModel):
    id: str
    provider_id: str
    provider_name: str = ""
    model_name: str
    display_name: str
    capabilities: dict
    is_active: bool
    sort_order: int
    created_at: str


class ModelTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: int = 0
