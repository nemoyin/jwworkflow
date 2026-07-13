"""工作流级文件上传 API"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.config import settings
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("/{workflow_id}/upload")
async def upload_workflow_file(
    workflow_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传文件到工作流临时存储"""
    # Validate file size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_bytes:
        raise HTTPException(status_code=413, detail=f"文件超过 {settings.MAX_FILE_SIZE_MB}MB")

    # Validate extension
    ext = os.path.splitext(file.filename or "unknown")[1].lower()
    allowed = {".xlsx", ".xls", ".csv", ".json", ".txt", ".pdf", ".docx"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    # Save to workflow temp dir
    upload_dir = os.path.join(settings.UPLOAD_DIR, "workflows", workflow_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_id = uuid.uuid4().hex[:12]
    stored_name = f"{file_id}{ext}"
    file_path = os.path.join(upload_dir, stored_name)

    with open(file_path, "wb") as f:
        import shutil
        shutil.copyfileobj(file.file, f)

    return {
        "file_id": file_id,
        "file_name": file.filename or stored_name,
        "file_path": file_path,
        "size": file_size,
        "mime_type": file.content_type or "application/octet-stream",
    }
