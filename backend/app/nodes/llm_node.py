"""LLM 节点：调用大语言模型推理（同步方式）"""

from openai import OpenAI

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


def _sync_chat_completion(
    messages: list[dict],
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """同步调用 OpenAI 兼容 API"""
    from app.config import settings

    client = OpenAI(
        api_key=api_key or settings.LLM_API_KEY,
        base_url=base_url or settings.LLM_BASE_URL,
    )
    response = client.chat.completions.create(
        model=model or settings.LLM_DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


class LLMNodeExecutor(BaseNodeExecutor):
    """LLM 节点：调用大语言模型推理（同步）"""

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
            content = _sync_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url=base_url,
            )
            return {"output": content, "model": model or ""}
        except Exception as e:
            import traceback
            return {"output": f"[LLM Error] {str(e)}", "model": model or "", "error": traceback.format_exc()}

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

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = asyncio.run_coroutine_threadsafe(_query(), loop)
                    return future.result(timeout=10)
            else:
                return loop.run_until_complete(_query())
        except Exception:
            return None, None
