"""Code Node — executes Python code in a sandboxed environment (with pandas support).

The executed code receives these pre-defined variables:

- ``ctx`` : ExecutionContext — workflow execution context
- ``config`` : dict — current node's configuration dict
- ``file_path`` : str — path to the uploaded data file (from upstream)
- ``pd`` : pandas module — for data analysis
- ``np`` : numpy module
- ``json`` : json module

The code must assign its result to ``result``.
If ``result`` is a dict, it is returned as-is; otherwise wrapped as ``{"output": result}``.
"""

import json as _json

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext

# Modules that can be imported inside the sandbox
_SAFE_MODULES = {
    "json": _json,
    "math": __import__("math"),
    "datetime": __import__("datetime"),
    "re": __import__("re"),
    "collections": __import__("collections"),
    "itertools": __import__("itertools"),
    "functools": __import__("functools"),
    "os": __import__("os"),
}

# Try to import pandas/numpy (might not be installed in all environments)
try:
    import pandas as _pd
    _SAFE_MODULES["pandas"] = _pd
    _SAFE_MODULES["pd"] = _pd
except ImportError:
    pass
try:
    import numpy as _np
    _SAFE_MODULES["numpy"] = _np
    _SAFE_MODULES["np"] = _np
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Allowed builtins
# ---------------------------------------------------------------------------
_ALLOWED_BUILTINS = {
    "True": True, "False": False, "None": None,
    "abs": abs, "all": all, "any": any, "bool": bool, "chr": chr,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset,
    "hasattr": hasattr, "hash": hash, "hex": hex, "id": id, "int": int,
    "isinstance": isinstance, "issubclass": issubclass, "iter": iter,
    "len": len, "list": list, "map": map, "max": max, "min": min,
    "next": next, "object": object, "oct": oct, "ord": ord,
    "pow": pow, "print": print, "range": range, "repr": repr,
    "reversed": reversed, "round": round, "set": set, "slice": slice,
    "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
    "type": type, "zip": zip,
    "__import__": __import__,  # needed for module imports
}


class CodeNodeExecutor(BaseNodeExecutor):
    """代码节点：在沙箱中执行 Python 代码（支持 pandas 数据分析）

    Config
    ------
    code : str
        Python 源代码。代码中可用的预定义变量：

        - ``ctx`` : ExecutionContext
        - ``config`` : dict
        - ``file_path`` : str — 上传的数据文件路径
        - ``pd`` : pandas 模块（如已安装）
        - ``np`` : numpy 模块（如已安装）
        - ``json`` : json 模块

        代码执行完毕后应将结果赋值给 ``result`` 变量。
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        # ---- Resolve file_path FIRST (before any code processing) ----
        raw_fp = config.get("file_path", "")
        if isinstance(raw_fp, str) and "{{" in raw_fp:
            try:
                raw_fp = ctx.resolve_variable(raw_fp)
            except KeyError:
                pass
        file_path = raw_fp
        if not file_path:
            for val in ctx.inputs.values():
                if isinstance(val, str) and ("/" in val or "\\" in val):
                    if any(val.endswith(ext) for ext in [".xlsx", ".xls", ".csv"]):
                        file_path = val
                        break
                elif isinstance(val, dict) and val.get("file_path"):
                    file_path = val["file_path"]
                    break

        # ---- Get code ----
        code = config.get("code", "")
        # 如果 code 为空，尝试从上游 LLM 节点的输出获取
        if not code.strip():
            for nid in ["n3", "code_gen", "llm_code"]:
                try:
                    out = ctx.get(nid)
                    candidate = out.get("output", out.get("code", ""))
                    if candidate and ("import" in candidate or "def " in candidate or "result " in candidate or "read_csv" in candidate or "read_excel" in candidate or "pandas" in candidate):
                        code = candidate
                        break
                except KeyError:
                    continue

        # 用实际文件路径替换 LLM 的 read 语句
        if code and file_path:
            import re, os as _os
            ext = _os.path.splitext(file_path)[1].lower()
            reader = "pd.read_excel" if ext in (".xlsx", ".xls") else "pd.read_csv"
            # Escape backslashes for regex replacement safety
            safe_path = file_path.replace("\\", "/")
            # 替换所有 pd.read_csv(...) 或 pd.read_excel(...)
            code = re.sub(r'pd\.(read_csv|read_excel)\([^)]*\)', f'{reader}(r"{safe_path}")', code)
            # 如果没有 read 语句，在最前面插入
            if reader.split(".")[1] not in code:
                code = f'import pandas as pd\ndf = {reader}(r"{safe_path}")\n' + code
        # Strip markdown code block markers (anywhere in code)
        code = code.strip()
        code = code.replace("```python\n", "").replace("```py\n", "").replace("```\n", "")
        code = code.replace("```python", "").replace("```py", "").replace("```", "").strip()

        if not code.strip():
            return {"output": "请提供要执行的代码，或确保上游 LLM 节点生成代码。"}

        # Build sandbox globals
        sandbox_globals: dict = {
            "__builtins__": _ALLOWED_BUILTINS,
            "ctx": ctx,
            "config": config,
            "file_path": file_path,
            "result": None,
        }
        sandbox_globals.update(_SAFE_MODULES)

        try:
            exec(code, sandbox_globals)
        except Exception as e:
            import traceback
            return {"error": f"{e}\n{traceback.format_exc()}", "success": False}

        result = sandbox_globals.get("result")
        # Serialize pandas objects
        if hasattr(_pd, "DataFrame") and isinstance(result, _pd.DataFrame):
            result = result.head(50).to_dict(orient="records")
        elif hasattr(_pd, "Series") and isinstance(result, _pd.Series):
            result = result.to_dict()

        if isinstance(result, dict):
            return result
        return {"output": result}
