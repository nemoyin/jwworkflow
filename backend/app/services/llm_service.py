"""LLM 服务：支持多供应商（兼容 OpenAI SDK）

通过 ModelRegistry 和 ModelProvider 数据库表管理多个 LLM 供应商。
同时保留配置文件中的 LLM_* 作为默认/降级配置。
"""

from openai import OpenAI
from app.config import settings

_client: OpenAI | None = None
_client_providers: dict[str, OpenAI] = {}  # provider_id -> client


def get_client() -> OpenAI:
    """获取默认 OpenAI 兼容客户端（基于配置文件的 LLM_* 设置）"""
    global _client
    if _client is None:
        if not settings.LLM_API_KEY:
            raise ValueError(
                "LLM_API_KEY 未配置。请在 .env 文件中设置，"
                "或通过模型管理页面添加供应商。"
            )
        _client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
    return _client


def get_provider_client(api_key: str, base_url: str) -> OpenAI:
    """基于 API Key 和 Base URL 创建客户端"""
    return OpenAI(api_key=api_key, base_url=base_url)


def reset_client():
    """重置所有客户端缓存（配置更新后调用）"""
    global _client, _client_providers
    _client = None
    _client_providers = {}


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    stream: bool = False,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """发送聊天补全请求

    Args:
        messages: 消息列表
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大输出 token 数
        stream: 是否流式输出
        api_key: 指定 API Key（用于多供应商场景）
        base_url: 指定 Base URL

    Returns:
        模型返回的文本内容
    """
    if api_key and base_url:
        client = get_provider_client(api_key, base_url)
    else:
        client = get_client()

    model = model or settings.LLM_DEFAULT_MODEL

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
    )

    if stream:
        collected = []
        for chunk in response:
            if chunk.choices[0].delta.content:
                collected.append(chunk.choices[0].delta.content)
        return "".join(collected)
    else:
        return response.choices[0].message.content or ""


async def chat_completion_with_tools(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    api_key: str | None = None,
    base_url: str | None = None,
) -> tuple[str, list[dict] | None]:
    """发送聊天补全请求（支持工具调用）

    Returns:
        (content, tool_calls): 返回内容和工具调用列表
    """
    if api_key and base_url:
        client = get_provider_client(api_key, base_url)
    else:
        client = get_client()

    model = model or settings.LLM_DEFAULT_MODEL

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message

    tool_calls = None
    if message.tool_calls:
        tool_calls = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]

    return message.content or "", tool_calls


async def chat_completion_by_model_id(
    model_id: str,
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """通过数据库中的模型 ID 发送聊天补全请求

    自动查找模型所属供应商的 API Key 和 Base URL。
    """
    from sqlalchemy import select
    from app.database import async_session
    from app.models.model_provider import ModelProvider
    from app.models.model_registry import ModelRegistry

    async with async_session() as db:
        result = await db.execute(
            select(ModelRegistry, ModelProvider)
            .join(ModelProvider, ModelRegistry.provider_id == ModelProvider.id)
            .where(ModelRegistry.id == model_id)
        )
        row = result.one_or_none()

    if not row:
        return f"[Error] Model '{model_id}' not found in registry"

    model, provider = row

    if not provider.api_key:
        return f"[Error] Provider '{provider.name}' has no API Key configured"

    return await chat_completion(
        messages=messages,
        model=model.model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=provider.api_key,
        base_url=provider.base_url,
    )
