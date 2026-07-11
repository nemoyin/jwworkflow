"""CollusionAgent — 围串标分析 Agent (stub)."""

from app.agents.base_agent import BaseScenarioAgent


class CollusionAgent(BaseScenarioAgent):
    """围串标分析智能体

    分析投标人名单及关联信息，识别围标串标风险。
    当前为桩实现（stub），返回模拟结果。

    Input
    -----
    bidder_list : list[dict]
        投标人列表，每项应含：
        - ``name``: 投标人名称
        - ``credit_code``: 统一社会信用代码（可选）
        - ``contact``: 联系方式（可选）

    Output
    ------
    risk_level : str
        风险等级（``"high"``, ``"medium"``, ``"low"``）。
    indicators : list[dict]
        识别出的围串标指标，每项含：
        - ``type``: 指标类型
        - ``description``: 指标描述
        - ``confidence``: 置信度（0.0 ~ 1.0）
        - ``involved_parties``: 涉及方列表
    """

    @property
    def name(self) -> str:
        return "collusion"

    @property
    def description(self) -> str:
        return (
            "分析多个投标人之间的关联关系，识别围标串标风险指标。"
            "输入参数: bidder_list (list[dict]) — 投标人列表。"
        )

    async def execute(self, params: dict) -> dict:
        bidder_list = params.get("bidder_list", [])
        if not bidder_list:
            return {"error": "Missing required parameter: bidder_list"}

        # Stub: simulate collusion analysis
        return {
            "risk_level": "high",
            "indicators": [
                {
                    "type": "MAC地址相同",
                    "description": "投标人A和投标人B的投标文件上传IP/MAC地址相同。",
                    "confidence": 0.95,
                    "involved_parties": [
                        bidder_list[0].get("name", "投标人A"),
                        bidder_list[1].get("name", "投标人B"),
                    ],
                },
                {
                    "type": "董监高交叉任职",
                    "description": "投标人C的监事同时在投标人D担任董事。",
                    "confidence": 0.82,
                    "involved_parties": [
                        bidder_list[2].get("name", "投标人C") if len(bidder_list) > 2 else "投标人C",
                        bidder_list[3].get("name", "投标人D") if len(bidder_list) > 3 else "投标人D",
                    ],
                },
                {
                    "type": "文件相似度过高",
                    "description": "投标人A和投标人C的技术方案文本相似度达98%。",
                    "confidence": 0.91,
                    "involved_parties": [
                        bidder_list[0].get("name", "投标人A"),
                        bidder_list[2].get("name", "投标人C") if len(bidder_list) > 2 else "投标人C",
                    ],
                },
            ],
        }

    def _input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "bidder_list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "投标人名称",
                            },
                            "credit_code": {
                                "type": "string",
                                "description": "统一社会信用代码",
                            },
                        },
                    },
                    "description": "投标人信息列表",
                },
            },
            "required": ["bidder_list"],
        }
