"""Code Node — executes Python code in a sandboxed environment.

The executed code receives ``ctx`` (ExecutionContext) and ``config`` (dict)
as pre-defined variables. It must assign its result to a ``result`` variable.

If ``result`` is a dict, it is returned as-is; otherwise it is wrapped as
``{"output": result}``.
"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext

# ---------------------------------------------------------------------------
# Allowed builtins — a restricted subset for safety.
# ---------------------------------------------------------------------------
_ALLOWED_BUILTINS = {
    # constants
    "True": True,
    "False": False,
    "None": None,
    # functions
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "chr": chr,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "hasattr": hasattr,
    "hash": hash,
    "hex": hex,
    "id": id,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "object": object,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "print": print,
    "range": range,
    "repr": repr,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
}


class CodeNodeExecutor(BaseNodeExecutor):
    """代码节点：在沙箱中执行 Python 代码

    Config
    ------
    code : str
        Python 源代码。代码中可用的预定义变量：

        - ``ctx`` : ExecutionContext — 工作流执行上下文
        - ``config`` : dict — 当前节点的配置字典

        代码执行完毕后应将结果赋值给 ``result`` 变量。
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        code = config.get("code", "")
        if not code.strip():
            return {"output": ""}

        # Build a restricted sandbox globals dict
        sandbox_globals: dict = {
            "__builtins__": _ALLOWED_BUILTINS,
            "ctx": ctx,
            "config": config,
            "result": None,
        }

        try:
            exec(code, sandbox_globals)
        except Exception as e:
            return {"error": str(e), "success": False}

        result = sandbox_globals.get("result")
        if isinstance(result, dict):
            return result
        return {"output": result}
