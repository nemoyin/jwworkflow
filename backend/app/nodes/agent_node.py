"""Agent Node — uses LLM reasoning to select and call tools.

MVP phase uses a stub implementation that simulates tool selection via a
configurable tool-call sequence (``_stub_tool_calls``). Phase 6 Task 2 will
integrate a real LLM API.

Execution flow
--------------
1. Build system prompt with tool descriptions
2. Call LLM (stub for MVP — returns simulated tool selection)
3. If LLM selects a tool, look up the tool definition
4. Execute the tool (HTTP call via httpx or code execution)
5. Return result to LLM for next iteration
6. Repeat until LLM returns final answer or max_iterations reached

Returns
-------
{"final_answer": "...", "tool_calls": [...], "iterations": N}
"""

import json

import httpx

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext
from app.schemas.tool import ToolDefinition


class AgentNodeExecutor(BaseNodeExecutor):
    """Agent 节点：使用 LLM 推理选择并调用工具

    MVP 阶段为桩实现（stub），使用预定义的工具调用序列模拟 LLM 行为。
    Phase 6 Task 2 将接入真实 LLM API。

    Config
    ------
    system_prompt : str
        系统提示词
    tools : list[dict | ToolDefinition]
        可用工具定义列表
    model : str, optional
        模型名称（默认 ``"default"``）
    max_iterations : int, optional
        最大迭代次数（默认 5）

    Stub 调试参数（仅 MVP 阶段）
    ------------------------------
    _stub_tool_calls : list[dict], optional
        模拟的工具调用序列（每项含 ``name`` 和 ``arguments``），
        执行完毕后自动返回 final_answer。
        ``None`` 或空列表表示直接返回 final_answer。
    """

    DEFAULT_MAX_ITERATIONS = 5

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        tools_raw = config.get("tools", [])
        model = config.get("model", "default")
        max_iterations = config.get("max_iterations", self.DEFAULT_MAX_ITERATIONS)

        # Parse tool definitions
        tool_defs = self._parse_tools(tools_raw)

        # Build initial prompt with tool descriptions
        full_prompt = self._build_prompt(system_prompt, tool_defs)

        # Stub: simulate LLM conversation with predefined tool call sequence
        stub_tool_calls = config.get("_stub_tool_calls", None)

        conversation = [
            {"role": "system", "content": full_prompt},
        ]

        tool_calls = []
        iterations = 0

        for iterations in range(max_iterations):
            # Call LLM (stub for MVP)
            response = self._call_llm_stub(
                conversation,
                model,
                stub_tool_calls,
                iterations,
                tool_calls,
            )

            if response["type"] == "final_answer":
                return {
                    "final_answer": response["content"],
                    "tool_calls": tool_calls,
                    "iterations": iterations + 1,
                }

            if response["type"] == "tool_call":
                tool_name = response["tool"]
                tool_args = response.get("arguments", {})

                tool_call_entry = {"name": tool_name, "arguments": tool_args}
                tool_calls.append(tool_call_entry)

                # Look up the tool definition
                tool_def = self._find_tool(tool_defs, tool_name)
                if tool_def is None:
                    result = {
                        "error": (
                            f"Tool '{tool_name}' not found. "
                            f"Available tools: {[t.name for t in tool_defs]}"
                        )
                    }
                else:
                    try:
                        result = self._execute_tool(tool_def, tool_args, ctx)
                    except Exception as e:
                        result = {"error": f"Tool execution failed: {str(e)}"}

                # Feed result back to conversation for next iteration
                conversation.append({
                    "role": "assistant",
                    "content": json.dumps({"tool_call": tool_call_entry}),
                })
                conversation.append({
                    "role": "user",
                    "content": json.dumps({"tool_result": result}),
                })
            else:
                # Fallback: treat unknown response type as final
                return {
                    "final_answer": str(response.get("content", "")),
                    "tool_calls": tool_calls,
                    "iterations": iterations + 1,
                }

        # Max iterations reached without final answer
        return {
            "final_answer": "Max iterations reached without final answer.",
            "tool_calls": tool_calls,
            "iterations": max_iterations,
        }

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(system_prompt: str, tools: list[ToolDefinition]) -> str:
        """将系统提示词和工具描述拼接为完整提示词。"""
        if not tools:
            return system_prompt

        parts = [system_prompt, "", "Available tools:"]
        for t in tools:
            desc = f"- {t.name}: {t.description}"
            if t.input_schema:
                desc += (
                    f"\n  Input schema: {json.dumps(t.input_schema, ensure_ascii=False)}"
                )
            parts.append(desc)
        parts.append(
            "\nYou may call one tool per turn. "
            "When you have enough information, respond with your final answer."
        )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Stub LLM
    # ------------------------------------------------------------------

    @staticmethod
    def _call_llm_stub(
        conversation,
        model,
        stub_tool_calls,
        iteration,
        already_called,
    ):
        """Stub LLM 调用 — 模拟返回 final_answer 或 tool_call。

        Parameters
        ----------
        conversation : list[dict]
            当前对话历史（供未来真实 LLM 使用，stub 阶段不依赖）
        model : str
            模型名称
        stub_tool_calls : list[dict] | None
            预定义的工具调用序列
        iteration : int
            当前迭代轮次（0-based）
        already_called : list[dict]
            已调用的工具列表

        Returns
        -------
        dict
            ``{"type": "final_answer", "content": "..."}`` 或
            ``{"type": "tool_call", "tool": "...", "arguments": {...}}``
        """
        # stub_tool_calls is None or empty → final answer immediately
        if not stub_tool_calls:
            return {
                "type": "final_answer",
                "content": (
                    f"[Stub] This is a simulated response using model '{model}'."
                ),
            }

        # More stub calls remain → return the next one
        if iteration < len(stub_tool_calls):
            call = stub_tool_calls[iteration]
            return {
                "type": "tool_call",
                "tool": call["name"],
                "arguments": call.get("arguments", {}),
            }

        # All stub calls processed → final answer
        return {
            "type": "final_answer",
            "content": (
                f"[Stub] All tool calls processed. "
                f"Final answer using model '{model}'."
            ),
        }

    # ------------------------------------------------------------------
    # Tool helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_tools(tools: list) -> list[ToolDefinition]:
        """将原始工具配置解析为 ToolDefinition 对象列表。"""
        result = []
        for t in tools:
            if isinstance(t, ToolDefinition):
                result.append(t)
            elif isinstance(t, dict):
                result.append(ToolDefinition(**t))
            else:
                raise TypeError(f"Unsupported tool type: {type(t)}")
        return result

    @staticmethod
    def _find_tool(
        tools: list[ToolDefinition],
        name: str,
    ) -> ToolDefinition | None:
        """按名称查找工具定义。"""
        for t in tools:
            if t.name == name:
                return t
        return None

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    @classmethod
    def _execute_tool(
        cls,
        tool_def: ToolDefinition,
        arguments: dict,
        ctx: ExecutionContext,
    ) -> dict:
        """执行工具调用。

        根据工具定义的 endpoint 类型选择执行方式：
        - ``"code"`` → 执行沙箱 Python 代码
        - URL      → 发起 HTTP 请求
        """
        if tool_def.endpoint == "code":
            return cls._execute_code_tool(tool_def.name, arguments)

        return cls._execute_http_tool(tool_def, arguments)

    # ------------------------------------------------------------------
    # Code tool execution
    # ------------------------------------------------------------------

    @staticmethod
    def _execute_code_tool(tool_name: str, arguments: dict) -> dict:
        """执行代码型工具 —— 以参数为输入执行沙箱代码。

        ``arguments`` 中须包含 ``code`` 键，值为可执行 Python 代码。
        代码中可用的变量：各参数键值对。
        代码执行完毕后应将结果赋值给 ``result`` 变量。
        """
        code = arguments.get("code", "")
        if not code.strip():
            return {"error": f"Tool '{tool_name}': no 'code' in arguments"}

        # Build a restricted sandbox
        from app.nodes.code_executor import _ALLOWED_BUILTINS

        local_vars = {
            k: v
            for k, v in arguments.items()
            if k != "code"
        }
        sandbox_globals: dict = {
            "__builtins__": _ALLOWED_BUILTINS,
            **local_vars,
            "result": None,
        }

        try:
            exec(code, sandbox_globals)
        except Exception as e:
            return {"error": f"Code execution failed: {str(e)}", "success": False}

        result = sandbox_globals.get("result")
        if isinstance(result, dict):
            return result
        return {"output": result}

    # ------------------------------------------------------------------
    # HTTP tool execution
    # ------------------------------------------------------------------

    @staticmethod
    def _execute_http_tool(tool_def: ToolDefinition, arguments: dict) -> dict:
        """执行 HTTP 型工具 — 向指定 endpoint 发起 REST 请求。"""
        url = tool_def.endpoint
        method = tool_def.method.upper()

        body = arguments.get("body")
        headers = arguments.get("headers", {})

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    json=body if method in ("POST", "PUT", "PATCH") else None,
                    params=arguments.get("params", {}),
                    headers=headers,
                )

            return {
                "status_code": response.status_code,
                "body": AgentNodeExecutor._parse_response_body(response),
            }
        except httpx.TimeoutException:
            return {"status_code": 0, "error": "Request timed out"}
        except httpx.ConnectError as e:
            return {"status_code": 0, "error": f"Connection failed: {str(e)}"}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    @staticmethod
    def _parse_response_body(response: httpx.Response):
        """尝试解析 JSON 响应，否则返回文本。"""
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                return response.json()
            except (ValueError, TypeError):
                return response.text
        return response.text
