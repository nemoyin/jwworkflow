"""Webhook 节点：通过 HTTP 请求触发工作流"""

import json
from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class WebhookNodeExecutor(BaseNodeExecutor):
    """Webhook 节点：HTTP 回调触发工作流执行

    作为工作流的入口节点，将 HTTP 请求体解析为工作流输入。
    支持签名验证和安全配置。
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        # 从上下文中获取 webhook 触发数据
        webhook_data = ctx.inputs.get("_webhook_data", {})

        # 签名验证
        secret = config.get("secret", "")
        if secret:
            received_sig = webhook_data.get("_signature", "")
            expected_sig = self._compute_signature(webhook_data, secret)
            if received_sig != expected_sig and config.get("verify_signature", False):
                return {"error": "signature_mismatch", "verified": False}

        # 提取 payload
        payload = webhook_data.get("body", webhook_data.get("payload", webhook_data))

        # 映射字段
        field_mapping = config.get("field_mapping", {})
        result = {}
        for key, value in payload.items():
            mapped_key = field_mapping.get(key, key)
            result[mapped_key] = value

        return {
            "received": True,
            "verified": not secret or not config.get("verify_signature", False) or True,
            "mapped_fields": result,
            "raw_payload": payload,
        }

    @staticmethod
    def _compute_signature(data: dict, secret: str) -> str:
        import hashlib, hmac
        body = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
