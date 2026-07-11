"""Agent Node — uses real LLM (DeepSeek API) to select and call tools.

Execution flow
--------------
1. Build system prompt with tool descriptions
2. Call LLM with tool definitions
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
from app.services.llm_service import chat_completion_with_tools


class AgentNodeExecutor(BaseNodeExecutor):
    """Agent 节点：使用 LLM 推理选择并调用工具

    通过 OpenAI 兼容接口调用 DeepSeek API。
    若 LLM_API_KEY 未配置则自动降级为桩实现（stub）。

    Config
    ------
    system_prompt : str
        系统提示词
    tools : list[dict | ToolDefinition]
        可用工具定义列表
    model : str, optional
        模型名称（默认使用 settings.LLM_DEFAULT_MODEL）
    max_iterations : int, optional
        最大迭代次数（默认 5）
    temperature : float, optional
        温度参数（默认 0.3）
    """

    DEFAULT_MAX_ITERATIONS = 5
    DEFAULT_TEMPERATURE = 0.3

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        tools_raw = config.get("tools", [])
        model = config.get("model")
        max_iterations = config.get("max_iterations", self.DEFAULT_MAX_ITERATIONS)
        temperature = config.get("temperature", self.DEFAULT_TEMPERATURE)

        # 检查是否配置了 API Key
        from app.config import settings
        use_stub = config.get("stub_mode", False) or not settings.LLM_API_KEY

        # Parse tool definitions
        tool_defs = self._parse_tools(tools_raw)

        # Build initial prompt with tool descriptions
        full_prompt = self._build_prompt(system_prompt, tool_defs)

        # Convert tools to OpenAI-compatible format
        openai_tools = self._to_openai_tools(tool_defs) if tool_defs and not use_stub else None

        conversation = [
            {"role": "system", "content": full_prompt},
        ]

        tool_calls = []
        iterations = 0

        for iterations in range(max_iterations):
            if use_stub:
                # 降级为桩实现
                response = self._call_llm_stub(
                    conversation, model or "default",
                    config.get("_stub_tool_calls"), iterations, tool_calls,
                )
            else:
                # 真实 LLM 调用
                response = self._call_llm_real(
                    conversation, model, openai_tools, temperature,
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

                # Feed result back
                conversation.append({
                    "role": "assistant",
                    "content": json.dumps({"tool_call": tool_call_entry}),
                })
                conversation.append({
                    "role": "user",
                    "content": json.dumps({"tool_result": result}),
                })
            else:
                return {
                    "final_answer": str(response.get("content", "")),
                    "tool_calls": tool_calls,
                    "iterations": iterations + 1,
                }

        return {
            "final_answer": "Max iterations reached without final answer.",
            "tool_calls": tool_calls,
            "iterations": max_iterations,
        }

    # ------------------------------------------------------------------
    # Real LLM call
    # ------------------------------------------------------------------

    @staticmethod
    def _call_llm_real(
        conversation: list[dict],
        model: str | None,
        tools: list[dict] | None,
        temperature: float,
    ) -> dict:
        """通过 DeepSeek API 调用真实 LLM（同步方式）"""
        from app.nodes.llm_node import _sync_chat_completion
        from openai import OpenAI
        from app.config import settings

        try:
            client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
            )
            kwargs = {
                "model": model or settings.LLM_DEFAULT_MODEL,
                "messages": conversation,
                "temperature": temperature,
                "max_tokens": 4096,
            }
            if tools:
                kwargs["tools"] = tools

            response = client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            content = message.content or ""

            if message.tool_calls:
                tc = message.tool_calls[0]
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, KeyError):
                    args = {}
                return {
                    "type": "tool_call",
                    "tool": tc.function.name,
                    "arguments": args,
                }
            return {"type": "final_answer", "content": content}
        except Exception as e:
            return {"type": "final_answer", "content": f"[LLM Error] {str(e)}"}

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    @staticmethod
    def _to_openai_tools(tools: list[ToolDefinition]) -> list[dict]:
        """将 ToolDefinition 转换为 OpenAI-compatible tool 格式"""
        openai_tools = []
        for t in tools:
            tool = {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema or {"type": "object", "properties": {}},
                },
            }
            openai_tools.append(tool)
        return openai_tools

    @staticmethod
    def _build_prompt(system_prompt: str, tools: list[ToolDefinition]) -> str:
        """将系统提示词和工具描述拼接为完整提示词。"""
        if not tools:
            return system_prompt

        parts = [system_prompt, "", "Available tools:"]
        for t in tools:
            desc = f"- {t.name}: {t.description}"
            if t.input_schema:
                desc += f"\n  Input schema: {json.dumps(t.input_schema, ensure_ascii=False)}"
            parts.append(desc)
        parts.append(
            "\nYou may call one tool per turn. "
            "When you have enough information, respond with your final answer."
        )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Stub LLM (fallback when no API key)
    # ------------------------------------------------------------------

    @staticmethod
    def _call_llm_stub(conversation, model, stub_tool_calls, iteration, already_called):
        """Stub LLM 调用 — 模拟返回 final_answer 或 tool_call。"""
        if not stub_tool_calls:
            return {
                "type": "final_answer",
                "content": f"[Stub] Simulated response using model '{model}'.",
            }

        if iteration < len(stub_tool_calls):
            call = stub_tool_calls[iteration]
            return {"type": "tool_call", "tool": call["name"], "arguments": call.get("arguments", {})}

        return {"type": "final_answer", "content": f"[Stub] All tool calls processed. Final answer using model '{model}'."}

    # ------------------------------------------------------------------
    # Tool helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_tools(tools: list) -> list[ToolDefinition]:
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
    def _find_tool(tools: list[ToolDefinition], name: str) -> ToolDefinition | None:
        for t in tools:
            if t.name == name:
                return t
        return None

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    @classmethod
    def _execute_tool(cls, tool_def: ToolDefinition, arguments: dict, ctx: ExecutionContext) -> dict:
        if tool_def.endpoint == "code":
            return cls._execute_code_tool(tool_def.name, arguments)
        return cls._execute_http_tool(tool_def, arguments)

    @staticmethod
    def _execute_code_tool(tool_name: str, arguments: dict) -> dict:
        code = arguments.get("code", "")
        if not code.strip():
            return {"error": f"Tool '{tool_name}': no 'code' in arguments"}

        from app.nodes.code_executor import _ALLOWED_BUILTINS
        local_vars = {k: v for k, v in arguments.items() if k != "code"}
        sandbox_globals: dict = {"__builtins__": _ALLOWED_BUILTINS, **local_vars, "result": None}

        try:
            exec(code, sandbox_globals)
        except Exception as e:
            return {"error": f"Code execution failed: {str(e)}", "success": False}

        result = sandbox_globals.get("result")
        return result if isinstance(result, dict) else {"output": result}

    @staticmethod
    def _execute_http_tool(tool_def: ToolDefinition, arguments: dict) -> dict:
        url = tool_def.endpoint
        method = tool_def.method.upper()
        body = arguments.get("body")
        headers = arguments.get("headers", {})

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method, url=url,
                    json=body if method in ("POST", "PUT", "PATCH") else None,
                    params=arguments.get("params", {}),
                    headers=headers,
                )
            return {"status_code": response.status_code, "body": AgentNodeExecutor._parse_response_body(response)}
        except httpx.TimeoutException:
            return {"status_code": 0, "error": "Request timed out"}
        except httpx.ConnectError as e:
            return {"status_code": 0, "error": f"Connection failed: {str(e)}"}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    @staticmethod
    def _parse_response_body(response: httpx.Response):
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                return response.json()
            except (ValueError, TypeError):
                return response.text
        return response.text
