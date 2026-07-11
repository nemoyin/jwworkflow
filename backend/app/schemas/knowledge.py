from pydantic import BaseModel
from typing import Optional


class DocumentResponse(BaseModel):
    id: str
    name: str
    content_type: str
    file_size: int
    status: str
    error: Optional[str] = None
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
