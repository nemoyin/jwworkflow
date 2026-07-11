import os
import uuid
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.knowledge import DocumentResponse, DocumentListResponse
from app.config import settings
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload", status_code=201, response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文档到知识库"""
    # Validate file size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)  # seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # reset to beginning
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE_MB}MB)",
        )

    # Ensure upload directory exists
    tenant_dir = os.path.join(settings.KNOWLEDGE_DIR, str(current_user.tenant_id))
    os.makedirs(tenant_dir, exist_ok=True)

    # Generate unique filename to avoid conflicts
    file_id = uuid.uuid4()
    ext = os.path.splitext(file.filename or "unknown")[1]
    stored_name = f"{file_id}{ext}"
    file_path = os.path.join(tenant_dir, stored_name)

    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {e}",
        )

    content_type = file.content_type or "application/octet-stream"

    doc = Document(
        tenant_id=current_user.tenant_id,
        name=file.filename or "unknown",
        file_path=file_path,
        content_type=content_type,
        file_size=file_size,
        status="pending",
    )
    db.add(doc)
    await db.flush()

    # 触发文档处理管道 (解析 → 分块 → 嵌入 → 存储)
    rag = RAGService()
    await rag.process_document(doc.id, db)

    return DocumentResponse(
        id=str(doc.id),
        name=doc.name,
        content_type=doc.content_type,
        file_size=doc.file_size,
        status=doc.status,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库文档列表"""
    # Count total
    count_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.tenant_id == current_user.tenant_id
        )
    )
    total = count_result.scalar() or 0

    # Fetch documents
    result = await db.execute(
        select(Document)
        .where(Document.tenant_id == current_user.tenant_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=str(d.id),
                name=d.name,
                content_type=d.content_type,
                file_size=d.file_size,
                status=d.status,
                error=d.error,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
            )
            for d in documents
        ],
        total=total,
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除知识库文档"""
    result = await db.execute(
        select(Document).where(
            Document.id == uuid.UUID(document_id),
            Document.tenant_id == current_user.tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # Remove file from disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass  # Non-critical; record will be deleted anyway

    await db.delete(doc)
    await db.flush()
