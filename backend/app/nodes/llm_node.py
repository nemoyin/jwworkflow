"""LLM 节点：调用大语言模型推理（支持多供应商）"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext
from app.services.llm_service import chat_completion


class LLMNodeExecutor(BaseNodeExecutor):
    """LLM 节点：调用大语言模型推理

    支持多供应商：
    1. 先查询 ModelRegistry 查找模型所属供应商
    2. 使用供应商的 API Key 和 Base URL 调用
    3. 如果未在注册表中找到，降级使用默认配置
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        model = config.get("model")
        system_prompt = config.get("system_prompt", "")
        user_prompt = config.get("prompt", "")
        temperature = config.get("temperature", 0.3)
        max_tokens = config.get("max_tokens", 4096)

        # 解析模板变量
        try:
            if "{{" in user_prompt:
                user_prompt = ctx.resolve_variable(user_prompt)
            if "{{" in system_prompt:
                system_prompt = ctx.resolve_variable(system_prompt)
        except KeyError:
            pass

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # 查找模型所属供应商
        api_key, base_url = self._lookup_provider(model)

        try:
            content = chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url=base_url,
            )
            return {"output": content, "model": model or ""}
        except Exception as e:
            return {"output": f"[LLM Error] {str(e)}", "model": model or "", "error": str(e)}

    @staticmethod
    def _lookup_provider(model_name: str) -> tuple:
        """在 ModelRegistry 中查找模型所属供应商"""
        if not model_name:
            return None, None
        try:
            import asyncio
            from sqlalchemy import select
            from app.database import async_session
            from app.models.model_provider import ModelProvider
            from app.models.model_registry import ModelRegistry

            async def _query():
                async with async_session() as db:
                    result = await db.execute(
                        select(ModelProvider)
                        .join(ModelRegistry, ModelRegistry.provider_id == ModelProvider.id)
                        .where(ModelRegistry.model_name == model_name)
                    )
                    p = result.scalar_one_or_none()
                    return (p.api_key, p.base_url) if p and p.api_key else (None, None)

            return asyncio.get_event_loop().run_until_complete(_query())
        except Exception:
            return None, None
