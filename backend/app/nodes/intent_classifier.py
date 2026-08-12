"""IntentClassifier — 分析用户意图，决定走简单查询还是复杂分析。

简单查询（simple_query）：生成结构化查询 DSL，由下游 query-executor 安全执行。
复杂分析（complex_analysis）：生成 pandas 代码，由下游 query-executor 执行沙箱。
"""

import json

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


def _llm_chat(
    system: str,
    user: str,
    model: str = "deepseek-chat",
    temperature: float = 0.01,
) -> str:
    from openai import OpenAI
    from app.config import settings

    client = OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )
    resp = client.chat.completions.create(
        model=model or settings.LLM_DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=8192,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"


_OPERATOR_HELP = """
支持的过滤运算符：
  >   >=   <   <=   ==   !=
  in           — {"value": ["上海","北京"]}
  not_in
  contains     — 字符串包含  {"value": "科技"}
  between      — 数值区间    {"value": [100, 500]}
  is_empty / is_not_empty

聚合函数：count, sum, avg, min, max
排序方向：asc / desc
"""

_INTENT_SYSTEM_PROMPT = f"""你是数据分析意图识别助手。根据列信息和用户问题，判断意图并输出 JSON。

【simple_query 判断标准】
只要问题只需要以下操作之一或其组合，就属于简单查询：
- 按条件过滤（> < = != >= <= in not_in contains between is_empty）
- 排序（asc / desc）
- 分组聚合（group by + count/sum/avg/min/max）
- 列选择（只看某些列）
- 取前/后 N 条

【complex_analysis 判断标准】
需要写 Python 代码才能解决的问题：
- 需要新增计算列（如日期间隔天数 = B - A）
- 模式识别、异常检测、统计分析
- 多步推导、规则交叉判断（如"是否存在围标串标嫌疑"）
- 自定义业务逻辑

【输出格式 - simple_query】
{{
  "intent": "simple_query",
  "query_dsl": {{
    "select": ["列1", "列2"],
    "filter": [{{"column": "列名", "operator": ">", "value": 100}}],
    "order_by": [{{"column": "列名", "direction": "desc"}}],
    "group_by": {{
      "columns": ["分组列"],
      "aggregations": [{{"function": "count", "column": "*", "alias": "数量"}}]
    }},
    "limit": 100
  }},
  "reason": "简单说明"
}}
{_OPERATOR_HELP}
filter / order_by / group_by / select / limit 都是可选的，不需要的不要出现。
select 省略 = 选择所有列。limit 省略 = 不限制。

【输出格式 - complex_analysis】
{{
  "intent": "complex_analysis",
  "code": "import pandas as pd\\n# 直接使用 df 变量（已读取）\\n...\\nresult = ...",
  "reason": "为什么需要写代码",
  "analysis_hint": "分析思路提示（可选）"
}}

【复杂分析代码规范】
- 直接使用 df 变量（已由系统读取），不要重复读取文件
- 不要构造示例数据
- 必须将最终结果赋值给 result 变量
- result 可以是字符串、字典或列表
- 只输出代码字符串，不含 markdown 标记
"""


class IntentClassifierNodeExecutor(BaseNodeExecutor):
    """意图识别节点：分析用户问题，输出 DSL（简单查询）或 pandas 代码（复杂分析）"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        question = self._get_question(ctx, config)
        columns, summary = self._get_data_info(ctx)
        model = config.get("model", "deepseek-chat")

        if not question:
            return {"intent": "complex_analysis", "error": "未检测到用户问题"}

        col_str = ", ".join(columns) if columns else "（无列信息）"
        user_msg = (
            f"文件列名：{col_str}\n"
            f"数据概况：{summary or '（无）'}\n"
            f"用户问题：{question}\n\n"
            f"判断意图并按要求输出 JSON。"
        )

        try:
            raw = _llm_chat(system=_INTENT_SYSTEM_PROMPT, user=user_msg, model=model)
            result = json.loads(raw)
        except Exception as e:
            result = {"intent": "complex_analysis", "reason": f"LLM 解析失败: {e}"}

        intent = result.get("intent", "complex_analysis")
        output = {
            "intent": intent,
            "reason": result.get("reason", ""),
            "analysis_hint": result.get("analysis_hint", ""),
            "question": question,
            "columns": columns,
        }

        if intent == "simple_query":
            dsl = result.get("query_dsl", {})
            if not dsl or not isinstance(dsl, dict):
                output["intent"] = "complex_analysis"
                output["reason"] = "DSL 生成失败，降级为复杂分析"
            else:
                output["query_dsl"] = dsl
        else:
            # complex_analysis: pass through the generated code
            output["code"] = result.get("code", "")
            if not output["code"]:
                output["code"] = '# 代码生成失败，请检查列名后重试\nresult = {"error": "代码生成失败"}'

        return output

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_question(ctx: ExecutionContext, config: dict) -> str:
        question = config.get("question", "")
        if "{{" in str(question):
            try:
                question = ctx.resolve_variable(question)
            except KeyError:
                pass
        if not question:
            try:
                obj = ctx.get("n1")
                if isinstance(obj, dict):
                    question = obj.get("question", "")
            except KeyError:
                pass
        if not question:
            question = ctx.inputs.get("question", "")
        return str(question)

    @staticmethod
    def _get_data_info(ctx: ExecutionContext) -> tuple[list[str], str]:
        for nid in ("n2", "excel_parser", "data_source"):
            try:
                out = ctx.get(nid)
                return out.get("columns", []), str(out.get("summary", ""))
            except KeyError:
                continue
        return [], ""
