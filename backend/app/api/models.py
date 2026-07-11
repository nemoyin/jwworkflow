"""多模型管理 API"""

import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.model_provider import ModelProvider
from app.models.model_registry import ModelRegistry
from app.schemas.model_management import (
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ModelCreate, ModelUpdate, ModelResponse, ModelTestResponse,
)
from app.services.llm_service import chat_completion, reset_client

router = APIRouter(prefix="/api/admin", tags=["model-management"])


# ========== Provider CRUD ==========

@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 LLM 供应商列表"""
    result = await db.execute(
        select(ModelProvider).where(ModelProvider.tenant_id == current_user.tenant_id)
        .order_by(ModelProvider.sort_order, ModelProvider.created_at)
    )
    providers = result.scalars().all()

    responses = []
    for p in providers:
        count_result = await db.execute(
            select(func.count(ModelRegistry.id)).where(ModelRegistry.provider_id == p.id)
        )
        model_count = count_result.scalar() or 0
        responses.append(ProviderResponse(
            id=str(p.id), name=p.name, provider_type=p.provider_type,
            api_key="***" if p.api_key else "", base_url=p.base_url,
            is_active=p.is_active, sort_order=p.sort_order,
            created_at=p.created_at.isoformat(), model_count=model_count,
        ))
    return responses


@router.post("/providers", status_code=201, response_model=ProviderResponse)
async def create_provider(
    body: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 LLM 供应商"""
    provider = ModelProvider(
        tenant_id=current_user.tenant_id,
        name=body.name, provider_type=body.provider_type,
        api_key=body.api_key, base_url=body.base_url,
        is_active=body.is_active, sort_order=body.sort_order,
    )
    db.add(provider)
    await db.flush()
    return ProviderResponse(
        id=str(provider.id), name=provider.name,
        provider_type=provider.provider_type,
        api_key="***" if provider.api_key else "",
        base_url=provider.base_url,
        is_active=provider.is_active,
        sort_order=provider.sort_order,
        created_at=provider.created_at.isoformat(),
    )


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    body: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 LLM 供应商"""
    result = await db.execute(
        select(ModelProvider).where(
            ModelProvider.id == uuid.UUID(provider_id),
            ModelProvider.tenant_id == current_user.tenant_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if body.name is not None: provider.name = body.name
    if body.provider_type is not None: provider.provider_type = body.provider_type
    if body.api_key is not None: provider.api_key = body.api_key
    if body.base_url is not None: provider.base_url = body.base_url
    if body.is_active is not None: provider.is_active = body.is_active
    if body.sort_order is not None: provider.sort_order = body.sort_order
    await db.flush()

    reset_client()  # 清除客户端缓存，下次使用新配置

    return ProviderResponse(
        id=str(provider.id), name=provider.name,
        provider_type=provider.provider_type,
        api_key="***" if provider.api_key else "",
        base_url=provider.base_url,
        is_active=provider.is_active,
        sort_order=provider.sort_order,
        created_at=provider.created_at.isoformat(),
    )


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除 LLM 供应商"""
    result = await db.execute(
        select(ModelProvider).where(
            ModelProvider.id == uuid.UUID(provider_id),
            ModelProvider.tenant_id == current_user.tenant_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await db.delete(provider)
    await db.flush()


# ========== Model Registry CRUD ==========

@router.get("/models", response_model=list[ModelResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有可用模型"""
    result = await db.execute(
        select(ModelRegistry)
        .join(ModelProvider)
        .where(ModelProvider.tenant_id == current_user.tenant_id)
        .order_by(ModelRegistry.sort_order, ModelRegistry.model_name)
    )
    models = result.scalars().all()

    # Get provider names
    provider_ids = {m.provider_id for m in models}
    provider_result = await db.execute(
        select(ModelProvider).where(ModelProvider.id.in_(provider_ids))
    )
    providers = {p.id: p.name for p in provider_result.scalars().all()}

    return [
        ModelResponse(
            id=str(m.id), provider_id=str(m.provider_id),
            provider_name=providers.get(m.provider_id, ""),
            model_name=m.model_name,
            display_name=m.display_name or m.model_name,
            capabilities=m.capabilities or {},
            is_active=m.is_active, sort_order=m.sort_order,
            created_at=m.created_at.isoformat(),
        )
        for m in models
    ]


@router.post("/models", status_code=201, response_model=ModelResponse)
async def create_model(
    body: ModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """注册新模型"""
    # 验证 provider 属于当前租户
    result = await db.execute(
        select(ModelProvider).where(
            ModelProvider.id == uuid.UUID(body.provider_id),
            ModelProvider.tenant_id == current_user.tenant_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    model = ModelRegistry(
        provider_id=uuid.UUID(body.provider_id),
        model_name=body.model_name,
        display_name=body.display_name or body.model_name,
        capabilities=body.capabilities,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(model)
    await db.flush()

    return ModelResponse(
        id=str(model.id), provider_id=str(model.provider_id),
        provider_name=provider.name,
        model_name=model.model_name,
        display_name=model.display_name or model.model_name,
        capabilities=model.capabilities or {},
        is_active=model.is_active, sort_order=model.sort_order,
        created_at=model.created_at.isoformat(),
    )


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    body: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新模型信息"""
    result = await db.execute(
        select(ModelRegistry).join(ModelProvider).where(
            ModelRegistry.id == uuid.UUID(model_id),
            ModelProvider.tenant_id == current_user.tenant_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if body.display_name is not None: model.display_name = body.display_name
    if body.capabilities is not None: model.capabilities = body.capabilities
    if body.is_active is not None: model.is_active = body.is_active
    if body.sort_order is not None: model.sort_order = body.sort_order
    await db.flush()

    return ModelResponse(
        id=str(model.id), provider_id=str(model.provider_id),
        provider_name="", model_name=model.model_name,
        display_name=model.display_name or model.model_name,
        capabilities=model.capabilities or {},
        is_active=model.is_active, sort_order=model.sort_order,
        created_at=model.created_at.isoformat(),
    )


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除模型"""
    result = await db.execute(
        select(ModelRegistry).join(ModelProvider).where(
            ModelRegistry.id == uuid.UUID(model_id),
            ModelProvider.tenant_id == current_user.tenant_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(model)
    await db.flush()


# ========== 健康检查 ==========

@router.post("/models/{model_id}/test", response_model=ModelTestResponse)
async def test_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """测试模型连通性"""
    result = await db.execute(
        select(ModelRegistry).join(ModelProvider).where(
            ModelRegistry.id == uuid.UUID(model_id),
            ModelProvider.tenant_id == current_user.tenant_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # 查找 provider
    p_result = await db.execute(
        select(ModelProvider).where(ModelProvider.id == model.provider_id)
    )
    provider = p_result.scalar_one_or_none()
    if not provider or not provider.api_key:
        return ModelTestResponse(success=False, message="Provider API Key 未配置")

    # 临时配置并测试
    import os
    old_key = os.environ.get("LLM_API_KEY", "")
    old_base = os.environ.get("LLM_BASE_URL", "")
    try:
        os.environ["LLM_API_KEY"] = provider.api_key
        os.environ["LLM_BASE_URL"] = provider.base_url
        reset_client()

        start = time.time()
        result_text = chat_completion(
            messages=[{"role": "user", "content": "Hello, respond with 'OK' only."}],
            model=model.model_name,
            max_tokens=10,
        )
        latency = int((time.time() - start) * 1000)
        return ModelTestResponse(success=True, message=f"响应成功: {result_text[:50]}", latency_ms=latency)
    except Exception as e:
        return ModelTestResponse(success=False, message=f"连接失败: {str(e)}")
    finally:
        os.environ["LLM_API_KEY"] = old_key
        os.environ["LLM_BASE_URL"] = old_base
        reset_client()


# ========== 前端下拉用 ==========

@router.get("/models/available", response_model=list[dict])
async def get_available_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取可供前端下拉选择的模型列表（简化格式）"""
    result = await db.execute(
        select(ModelRegistry).join(ModelProvider).where(
            ModelRegistry.is_active == True,
            ModelProvider.tenant_id == current_user.tenant_id,
            ModelProvider.is_active == True,
        ).order_by(ModelRegistry.sort_order, ModelRegistry.model_name)
    )
    models = result.scalars().all()

    # Get provider names
    pids = {m.provider_id for m in models}
    pr = await db.execute(select(ModelProvider).where(ModelProvider.id.in_(pids)))
    providers = {p.id: p.name for p in pr.scalars().all()}

    return [
        {
            "id": str(m.id),
            "label": f"{providers.get(m.provider_id, '?')} / {m.display_name or m.model_name}",
            "model_name": m.model_name,
            "provider_id": str(m.provider_id),
            "supports_tools": (m.capabilities or {}).get("tool_calls", False),
            "supports_streaming": (m.capabilities or {}).get("streaming", False),
            "max_tokens": (m.capabilities or {}).get("max_tokens", 4096),
        }
        for m in models
    ]
