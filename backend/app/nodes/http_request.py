"""HTTP Request Node — makes REST API calls.

Supports GET / POST / PUT / PATCH / DELETE / HEAD / OPTIONS.
Supports variable resolution in URL, headers, and body via template syntax.
"""

import json

import httpx

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


def _resolve_val(ctx: ExecutionContext, value: object) -> object:
    """Resolve a config value if it contains template syntax."""
    if isinstance(value, str) and "{{" in value:
        return ctx.resolve_variable(value)
    return value


def _resolve_dict(
    ctx: ExecutionContext, d: dict[str, object]
) -> dict[str, object]:
    """Resolve all values in a dict that contain template syntax."""
    resolved: dict[str, object] = {}
    for k, v in d.items():
        rk = _resolve_val(ctx, k) if isinstance(k, str) else k
        rv: object
        if isinstance(v, str) and "{{" in v:
            rv = ctx.resolve_variable(v)
        elif isinstance(v, dict):
            rv = _resolve_dict(ctx, v)
        else:
            rv = v
        resolved[str(rk)] = rv
    return resolved


class HttpRequestNodeExecutor(BaseNodeExecutor):
    """HTTP 请求节点：发起 REST API 调用

    Config
    ------
    method : str
        HTTP 方法：GET / POST / PUT / PATCH / DELETE / HEAD / OPTIONS
    url : str
        请求 URL（支持模板变量）
    headers : dict, optional
        请求头字典（值支持模板变量）
    body : dict or str, optional
        请求体。dict 会被序列化为 JSON；str 支持模板变量
    auth : dict, optional
        认证配置（当前支持 ``{"type": "basic", "username": "...", "password": "..."}``）
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        method = config.get("method", "GET").upper()
        url = _resolve_val(ctx, config.get("url", ""))
        headers = _resolve_dict(ctx, config.get("headers", {}))
        body = config.get("body")
        auth = config.get("auth")

        # Resolve body
        json_body: object = None
        data_body: str | None = None
        if body is not None:
            if isinstance(body, dict):
                json_body = _resolve_dict(ctx, body)
            elif isinstance(body, str):
                data_body = str(_resolve_val(ctx, body))
            else:
                data_body = str(body)

        # Auth
        auth_tuple: tuple[str, str] | None = None
        if auth and auth.get("type") == "basic":
            auth_tuple = (auth.get("username", ""), auth.get("password", ""))

        try:
            with httpx.Client() as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_body if method in ("POST", "PUT", "PATCH") else None,
                    data=data_body if method in ("POST", "PUT", "PATCH") and json_body is None else None,
                    auth=auth_tuple,
                    timeout=30,
                )
        except httpx.TimeoutException:
            return {"status_code": 0, "error": "Request timed out", "body": None}
        except httpx.RequestError as e:
            return {"status_code": 0, "error": f"Request failed: {e}", "body": None}

        # Parse response body
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body_result: object = response.json()
            except (json.JSONDecodeError, ValueError):
                body_result = response.text
        else:
            body_result = response.text

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body_result,
        }
