"""QueryExecutor — 分发执行器：根据上游 intent-classifier 的输出选择执行路径。

简单查询（simple_query）：安全执行结构化 DSL（filter / sort / group_by / select），无需 exec()。
复杂分析（complex_analysis）：调用 LLM 生成 pandas 代码并执行（回退到原 CodeNode 逻辑）。
"""

import os as _os

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class QueryExecutorNodeExecutor(BaseNodeExecutor):
    """查询执行节点：根据意图自动选择执行路径"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        # ---- 获取上游意图 ----
        intent_info = self._get_intent_info(ctx, config)
        intent = intent_info.get("intent", "")

        if intent == "simple_query":
            return self._execute_simple(ctx, config, intent_info)
        elif intent == "complex_analysis":
            return self._execute_complex(ctx, config, intent_info)
        else:
            return {"error": f"未知意图: {intent}", "intent": intent}

    # ------------------------------------------------------------------
    # 简单查询路径：安全执行 DSL
    # ------------------------------------------------------------------
    def _execute_simple(self, ctx, config, intent_info: dict) -> dict:
        import pandas as pd

        dsl = intent_info.get("query_dsl", {})
        file_path = self._get_file_path(ctx, config)
        if not file_path or not _os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}", "rows": [], "row_count": 0}

        df = self._load_file(file_path)
        if df is None:
            return {"error": "文件加载失败", "rows": [], "row_count": 0}

        try:
            df = self._apply_select(df, dsl)
            df = self._apply_filter(df, dsl)
            df = self._apply_group_by(df, dsl)
            df = self._apply_order_by(df, dsl)
            df = self._apply_limit(df, dsl)
        except Exception as e:
            return {"error": f"DSL 执行失败: {e}", "rows": [], "row_count": 0}

        from app.nodes.code_executor import _make_json_safe

        total = len(df)
        rows = _make_json_safe(df.head(20).to_dict(orient="records"))

        result = {
            "intent": "simple_query",
            "rows": rows,
            "row_count": total,
            "display_count": len(rows),
            "columns": list(df.columns),
            "truncated": total > 500,
        }
        if dsl.get("group_by"):
            result["summary"] = f"共 {total} 条分组结果"
        return result

    # ------------------------------------------------------------------
    # 复杂分析路径：生成代码 → 执行（复用 CodeNode 逻辑）
    # ------------------------------------------------------------------
    def _execute_complex(self, ctx, config, intent_info: dict) -> dict:
        import re

        question = intent_info.get("question", ctx.inputs.get("question", ""))
        hint = intent_info.get("analysis_hint", "")
        columns = intent_info.get("columns", [])
        file_path = self._get_file_path(ctx, config)

        # 调用 LLM 生成代码
        code = self._generate_code(question, columns, hint, config)
        if not code:
            return {"intent": "complex_analysis", "error": "代码生成失败"}

        # 执行代码（复用 code_executor 的沙箱逻辑）
        from app.nodes.code_executor import CodeNodeExecutor, _make_json_safe

        # 构建一个临时的 code node config
        code_config = {"code": code, "file_path": file_path}
        sandbox_exec = CodeNodeExecutor()
        sandbox_result = sandbox_exec.execute(ctx, code_config)

        # 如果 code_executor 已经内置了 _make_json_safe，就不需要额外处理
        # 但我们确保返回结果也做一层安全转换
        safe_result = _make_json_safe(sandbox_result)

        return {
            "intent": "complex_analysis",
            "code": code,
            **safe_result,
        }

    # ------------------------------------------------------------------
    # LLM 代码生成
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_code(question: str, columns: list[str], hint: str, config: dict) -> str:
        from openai import OpenAI
        from app.config import settings

        col_str = ", ".join(columns) if columns else "（无列信息）"
        hint_str = f"\n分析思路提示：{hint}" if hint else ""

        system = (
            "你是数据分析代码生成助手。用户上传了 Excel 数据文件，代码中直接使用 df 变量（已读取）。\n"
            "生成 Python pandas 代码来分析数据。\n\n"
            "规则：\n"
            "1. 直接使用 df 变量操作数据，不要重新读取文件\n"
            "2. 不要构造示例数据\n"
            "3. 代码必须将最终结果赋值给 result 变量\n"
            "4. result 可以是字符串、字典或列表\n"
            "5. 只输出代码，不要解释"
        )
        user = (
            f"列名：{col_str}\n"
            f"用户问题：{question}\n"
            f"{hint_str}\n\n"
            "生成分析代码："
        )

        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        model = config.get("model", "deepseek-chat")
        try:
            resp = client.chat.completions.create(
                model=model or settings.LLM_DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            code = resp.choices[0].message.content or ""
            # Clean markdown fences
            code = code.replace("```python\n", "").replace("```py\n", "").replace("```\n", "")
            code = code.replace("```python", "").replace("```py", "").replace("```", "").strip()
            return code
        except Exception as e:
            return f"# LLM 代码生成失败: {e}"

    # ------------------------------------------------------------------
    # 文件加载
    # ------------------------------------------------------------------
    @staticmethod
    def _load_file(file_path: str):
        import pandas as pd
        ext = _os.path.splitext(file_path)[1].lower()
        try:
            if ext in (".xlsx", ".xls"):
                return pd.read_excel(file_path)
            elif ext == ".csv":
                for enc in ["utf-8", "gbk", "gb2312", "gb18030", "utf-16"]:
                    try:
                        return pd.read_csv(file_path, encoding=enc)
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                return pd.read_csv(file_path, encoding="utf-8", encoding_errors="replace")
        except Exception:
            return None
        return None

    # ------------------------------------------------------------------
    # DSL 操作链
    # ------------------------------------------------------------------
    @staticmethod
    def _apply_select(df, dsl: dict):
        select = dsl.get("select")
        if select and isinstance(select, list):
            valid = [c for c in select if c in df.columns]
            if valid:
                df = df[valid]
        return df

    @staticmethod
    def _apply_filter(df, dsl: dict):
        import pandas as pd
        filters = dsl.get("filter", [])
        for f in filters:
            col = f.get("column", "")
            op = f.get("operator", "")
            val = f.get("value")
            if col not in df.columns:
                continue
            if op == ">":
                df = df[pd.to_numeric(df[col], errors="coerce") > float(val)]
            elif op == ">=":
                df = df[pd.to_numeric(df[col], errors="coerce") >= float(val)]
            elif op == "<":
                df = df[pd.to_numeric(df[col], errors="coerce") < float(val)]
            elif op == "<=":
                df = df[pd.to_numeric(df[col], errors="coerce") <= float(val)]
            elif op == "==":
                df = df[df[col].astype(str) == str(val)]
            elif op == "!=":
                df = df[df[col].astype(str) != str(val)]
            elif op == "in":
                if isinstance(val, list):
                    df = df[df[col].isin(val)]
            elif op == "not_in":
                if isinstance(val, list):
                    df = df[~df[col].isin(val)]
            elif op == "contains":
                df = df[df[col].astype(str).str.contains(str(val), na=False)]
            elif op == "between":
                if isinstance(val, list) and len(val) == 2:
                    num = pd.to_numeric(df[col], errors="coerce")
                    df = df[(num >= float(val[0])) & (num <= float(val[1]))]
            elif op == "is_empty":
                df = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
            elif op == "is_not_empty":
                df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
        return df

    @staticmethod
    def _apply_group_by(df, dsl: dict):
        import pandas as pd
        gb = dsl.get("group_by")
        if not gb or not isinstance(gb, dict):
            return df
        group_cols = gb.get("columns", [])
        aggs = gb.get("aggregations", [])
        valid_groups = [c for c in group_cols if c in df.columns]
        if not valid_groups:
            return df
        if not aggs:
            return df[valid_groups].drop_duplicates()
        agg_map = {}
        for a in aggs:
            func = a.get("function", "count")
            col = a.get("column", "*")
            alias = a.get("alias", f"{func}_{col}")
            if col == "*":
                if func == "count":
                    agg_map[alias] = pd.NamedAgg(column=valid_groups[0], aggfunc="count")
            elif col in df.columns:
                FN_MAP = {"count": "count", "sum": "sum", "avg": "mean", "mean": "mean", "min": "min", "max": "max"}
                fn = FN_MAP.get(func, "count")
                agg_map[alias] = pd.NamedAgg(column=col, aggfunc=fn)
        if agg_map:
            df = df.groupby(valid_groups, as_index=False).agg(**agg_map)
        return df

    @staticmethod
    def _apply_order_by(df, dsl: dict):
        order = dsl.get("order_by", [])
        if not order:
            return df
        by = []
        ascending = []
        for o in order:
            col = o.get("column", "")
            if col in df.columns:
                by.append(col)
                ascending.append(o.get("direction", "asc").lower() != "desc")
        if by:
            df = df.sort_values(by=by, ascending=ascending)
        return df

    @staticmethod
    def _apply_limit(df, dsl: dict):
        limit = dsl.get("limit", 0)
        if limit and isinstance(limit, (int, float)) and limit > 0:
            df = df.head(int(limit))
        return df

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_intent_info(ctx: ExecutionContext, config: dict) -> dict:
        """从上游 intent-classifier 节点获取意图信息"""
        # Direct invocation with override
        intent = config.get("intent", "")
        if intent:
            return {"intent": intent, "query_dsl": config.get("query_dsl", {})}
        # From upstream
        for nid in ("n3", "intent_classifier"):
            try:
                return ctx.get(nid)
            except KeyError:
                continue
        return {}

    @staticmethod
    def _get_file_path(ctx: ExecutionContext, config: dict) -> str:
        raw_fp = config.get("file_path", "")
        if isinstance(raw_fp, str) and "{{" in raw_fp:
            try:
                raw_fp = ctx.resolve_variable(raw_fp)
            except KeyError:
                pass
        if raw_fp:
            return raw_fp
        # Fallback: from inputs
        for val in ctx.inputs.values():
            if isinstance(val, str) and "/" in val:
                if any(val.endswith(ext) for ext in [".xlsx", ".xls", ".csv"]):
                    return val
            elif isinstance(val, dict) and val.get("file_path"):
                return val["file_path"]
        return ""
