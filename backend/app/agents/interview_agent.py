"""InterviewAgent — 纪检谈话 Agent (stub)."""

from app.agents.base_agent import BaseScenarioAgent


class InterviewAgent(BaseScenarioAgent):
    """纪检谈话智能体

    模拟纪检谈话场景，根据问题生成拟真的谈话回应。
    当前为桩实现（stub），返回模拟结果。

    Input
    -----
    question : str
        纪检人员的问题。
    context : dict, optional
        谈话上下文信息，可含：
        - ``case_description``: 案件描述
        - ``interviewee_name``: 被谈话人姓名
        - ``interviewee_role``: 被谈话人角色

    Output
    ------
    response : str
        模拟的谈话回应文本。
    emotional_state : str, optional
        模拟的情绪状态（仅 stub 阶段）。
    """

    @property
    def name(self) -> str:
        return "interview"

    @property
    def description(self) -> str:
        return (
            "模拟纪检谈话场景，基于问题生成拟真的谈话回应。"
            "输入参数: question (str) — 谈话问题；"
            "context (dict, optional) — 谈话上下文。"
        )

    async def execute(self, params: dict) -> dict:
        question = params.get("question", "")
        if not question:
            return {"error": "Missing required parameter: question"}

        context = params.get("context", {})
        interviewee_name = context.get("interviewee_name", "当事人")

        # Stub: simulate interview response
        return {
            "response": (
                f"我（{interviewee_name}）需要说明的是，在招标过程中我一直严格遵守"
                f"各项规定。对于您提到的这个问题，我没有什么需要隐瞒的。"
                f"当时我们按照正常流程完成了投标工作，所有文件都按规定留存备查。"
                f"如果您有具体的证据或线索，我愿意配合进一步调查。"
            ),
            "emotional_state": "平稳",
        }

    def _input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "纪检谈话问题",
                },
                "context": {
                    "type": "object",
                    "properties": {
                        "case_description": {
                            "type": "string",
                            "description": "案件描述",
                        },
                        "interviewee_name": {
                            "type": "string",
                            "description": "被谈话人姓名",
                        },
                        "interviewee_role": {
                            "type": "string",
                            "description": "被谈话人角色",
                        },
                    },
                    "description": "谈话上下文信息",
                },
            },
            "required": ["question"],
        }
