"""ExcelParserNode: 解析 Excel/CSV 文件为结构化数据"""

import os
import json
from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class ExcelParserNodeExecutor(BaseNodeExecutor):
    """Excel 解析节点：读取 Excel/CSV 文件，输出结构化 JSON + Markdown 表格"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        # Resolve template variables in config (e.g. {{ input.file_path }})
        resolved_config = {}
        for k, v in config.items():
            if isinstance(v, str) and "{{" in v:
                try:
                    resolved_config[k] = ctx.resolve_variable(v)
                except KeyError:
                    resolved_config[k] = v
            else:
                resolved_config[k] = v

        file_path = resolved_config.get("file_path", "")
        sheet_name = resolved_config.get("sheet_name", None)
        max_rows = resolved_config.get("max_rows", 0)

        # Try to get file_path from upstream input node
        if not file_path:
            for key in ctx.inputs:
                val = ctx.inputs[key]
                if isinstance(val, dict) and val.get("file_path"):
                    file_path = val["file_path"]
                    break
                if isinstance(val, str) and os.path.exists(val):
                    file_path = val
                    break

        if not file_path or not os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}", "row_count": 0, "columns": [], "data_text": ""}

        ext = os.path.splitext(file_path)[1].lower()

        try:
            import pandas as pd

            if ext in (".xlsx", ".xls"):
                sheet_names = self._get_sheet_names(file_path)
                # sheet_name=None returns dict; use first sheet
                sn = sheet_name if sheet_name else (sheet_names[0] if sheet_names else 0)
                df = pd.read_excel(file_path, sheet_name=sn, dtype=str)
            elif ext == ".csv":
                # Auto-detect encoding (common Chinese encodings)
                df = None
                for enc in ["utf-8", "gbk", "gb2312", "gb18030", "utf-16"]:
                    try:
                        df = pd.read_csv(file_path, dtype=str, encoding=enc)
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                if df is None:
                    df = pd.read_csv(file_path, dtype=str, encoding="utf-8", encoding_errors="replace")
                sheet_names = []
            else:
                return {"error": f"不支持的文件类型: {ext}", "row_count": 0, "columns": [], "data_text": ""}

        except Exception as e:
            return {"error": f"解析失败: {str(e)}", "row_count": 0, "columns": [], "data_text": ""}

        if df.empty:
            return {"row_count": 0, "columns": [], "data_text": "（空文件）", "sheet_names": sheet_names}

        # Convert to preview + text
        total_rows = len(df)

        # 控制传给 LLM 的行数（max_rows=0 表示不限制）
        llm_limit = max_rows if max_rows > 0 else total_rows
        llm_rows = min(total_rows, llm_limit)
        display_df = df.head(llm_rows)

        columns = list(df.columns)
        header = "| " + " | ".join(str(c) for c in columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        rows_text = "\n".join(
            "| " + " | ".join(str(v) if pd.notna(v) else "" for v in row) + " |"
            for _, row in display_df.iterrows()
        )

        # 如果截断了，在表格开头注明
        is_truncated = llm_rows < total_rows
        truncated_note = f"\n> ⚠️ 数据共 {total_rows} 行，仅展示前 {llm_rows} 行。如需完整分析请使用 CodeNode 做聚合。\n" if is_truncated else ""
        data_text = f"{truncated_note}{header}\n{separator}\n{rows_text}"

        # Build preview JSON (仅前 20 行用于前端展示)
        preview = df.head(20).to_dict(orient="records")

        # Basic summary
        null_counts = df.isnull().sum().to_dict()
        dtypes = {str(c): str(df[c].dtype) for c in columns}
        summary = f"{total_rows} 行 × {len(columns)} 列"
        if is_truncated:
            summary += f"，展示了前 {llm_rows} 行"

        return {
            "columns": columns,
            "row_count": total_rows,
            "display_rows": llm_rows,
            "preview": preview,
            "data_text": data_text,
            "summary": summary,
            "dtypes": dtypes,
            "null_counts": {str(k): int(v) for k, v in null_counts.items()},
            "sheet_names": sheet_names,
        }

    @staticmethod
    def _get_sheet_names(file_path: str) -> list[str]:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            return wb.sheetnames
        except Exception:
            return []
