"""ComplianceAgent — 招标合规审查 Agent (stub)."""

from app.agents.base_agent import BaseScenarioAgent


class ComplianceAgent(BaseScenarioAgent):
    """招标合规审查智能体

    对招标文件进行合规性审查，识别潜在违规风险点。
    当前为桩实现（stub），返回模拟结果。

    Input
    -----
    document_text : str
        招标文件文本。

    Output
    ------
    score : float
        合规评分（0.0 ~ 1.0）。
    issues : list[dict]
        识别出的问题列表，每项含：
        - ``type``: 问题类型
        - ``description``: 问题描述
        - ``severity``: 严重程度（``"high"``, ``"medium"``, ``"low"``）
        - ``clause``: 相关条款原文（如有）
    """

    @property
    def name(self) -> str:
        return "compliance"

    @property
    def description(self) -> str:
        return (
            "审查招标文件的合规性，识别违规风险点并提供合规评分。"
            "输入参数: document_text (str) — 招标文件文本。"
        )

    async def execute(self, params: dict) -> dict:
        document_text = params.get("document_text", "")
        if not document_text:
            return {"error": "Missing required parameter: document_text"}

        # Stub: simulate compliance review
        return {
            "score": 0.85,
            "issues": [
                {
                    "type": "资格条件设置不当",
                    "description": "要求投标人注册资本不低于1000万元，可能构成不合理限制。",
                    "severity": "medium",
                    "clause": "投标人须具有1000万元（含）以上注册资本",
                },
                {
                    "type": "评分标准不明确",
                    "description": "技术方案评分标准缺少量化指标，主观性过强。",
                    "severity": "high",
                    "clause": "技术方案（30分）：由评委根据方案的合理性、可行性综合评分",
                },
                {
                    "type": "工期设置不合理",
                    "description": "招标文件要求的工期（30天）明显短于行业平均水平（60天）。",
                    "severity": "low",
                    "clause": "交货期：合同签订后30日内完成交付",
                },
            ],
        }

    def _input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "document_text": {
                    "type": "string",
                    "description": "招标文件文本内容",
                },
            },
            "required": ["document_text"],
        }
