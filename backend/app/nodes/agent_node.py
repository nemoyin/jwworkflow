"""Agent Node — ReAct / Function Calling dual-mode agent.

Supports two reasoning modes:

- **function_calling** (default): Uses OpenAI-compatible tool definitions.
  The LLM selects tools via ``tool_calls`` and returns results.

- **react**: Uses a structured ReAct prompt (Thought/Action/Action Input/
  Observation). Responses are parsed from the LLM's text output.

Returns
-------
{"final_answer": "...", "tool_calls": [...], "iterations": N,
 "trace": [...]}   (trace only present in react mode)
"""

import json
import re

import httpx

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext
from app.schemas.tool import ToolDefinition
from app.services.llm_service import chat_completion_with_tools

# ReAct prompt template
REACT_SYSTEM_TEMPLATE = """You are an AI assistant that follows the ReAct pattern.

You have access to the following tools:

{tool_descriptions}

Use the following format exactly:

Thought: what you need to do
Action: the tool name to call
Action Input: the input for the tool (as a JSON object)
Observation: the result of the tool action
... (this Thought/Action/Action Input/Observation can repeat)
Thought: I now have the final answer
Final Answer: your response

If you don't need to use any tools, respond with:
Thought: I don't need tools for this
Final Answer: your response"""


class AgentNodeExecutor(BaseNodeExecutor):
    """Agent 节点：ReAct / Function Calling 双模式

    Config
    ------
    system_prompt : str
        系统提示词
    tools : list[dict | ToolDefinition]
        可用工具定义列表
    model : str, optional
        模型名称
    max_iterations : int, optional
        最大迭代次数（默认 10）
    temperature : float, optional
        温度参数（默认 0.3）
    mode : str, optional
        "function_calling" (默认) 或 "react"
    """

    DEFAULT_MAX_ITERATIONS = 10
    DEFAULT_TEMPERATURE = 0.3

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        # Resolve template variables in system_prompt (e.g. {{ input.scenario }})
        if "{{" in system_prompt:
            system_prompt = ctx.resolve_variable(system_prompt)
        tools_raw = config.get("tools", [])
        model = config.get("model")
        max_iterations = config.get("max_iterations", self.DEFAULT_MAX_ITERATIONS)
        temperature = config.get("temperature", self.DEFAULT_TEMPERATURE)
        mode = config.get("mode", "function_calling")

        from app.config import settings
        use_stub = config.get("stub_mode", False) or not settings.LLM_API_KEY

        tool_defs = self._parse_tools(tools_raw)

        if mode == "react":
            return self._execute_react(system_prompt, tool_defs, model, max_iterations, temperature, ctx, use_stub, config)

        # --- function_calling mode (original) ---
        full_prompt = self._build_prompt(system_prompt, tool_defs)
        openai_tools = self._to_openai_tools(tool_defs) if tool_defs and not use_stub else None
        conversation = [{"role": "system", "content": full_prompt}]
        tool_calls = []

        for iterations in range(max_iterations):
            if use_stub:
                resp = self._call_llm_stub(conversation, model or "default", config.get("_stub_tool_calls"), iterations, tool_calls)
            else:
                resp = self._call_llm_real(conversation, model, openai_tools, temperature)

            if resp["type"] == "final_answer":
                return {"final_answer": resp["content"], "tool_calls": tool_calls, "iterations": iterations + 1}

            if resp["type"] == "tool_call":
                tool_calls.append({"name": resp["tool"], "arguments": resp.get("arguments", {})})
                tool_def = self._find_tool(tool_defs, resp["tool"])
                result = {"error": f"Tool '{resp['tool']}' not found"} if tool_def is None else self._execute_tool(tool_def, resp.get("arguments", {}), ctx)
                conversation.append({"role": "assistant", "content": json.dumps({"tool_call": {"name": resp["tool"], "arguments": resp.get("arguments", {})}})})
                conversation.append({"role": "user", "content": json.dumps({"tool_result": result})})
            else:
                return {"final_answer": str(resp.get("content", "")), "tool_calls": tool_calls, "iterations": iterations + 1}

        return {"final_answer": "Max iterations reached.", "tool_calls": tool_calls, "iterations": max_iterations}

    def _execute_react(self, system_prompt, tool_defs, model, max_iterations, temperature, ctx, use_stub, config):
        """ReAct 模式：Thought → Action → Observation 循环"""
        # Build ReAct prompt
        tool_lines = []
        for t in tool_defs:
            tool_lines.append(f"- {t.name}: {t.description}")
            if t.input_schema:
                tool_lines.append(f"  Input: {json.dumps(t.input_schema, ensure_ascii=False)}")
        tool_desc = "\n".join(tool_lines) if tool_lines else "No tools available."

        prompt = REACT_SYSTEM_TEMPLATE.replace("{tool_descriptions}", tool_desc)
        if system_prompt and system_prompt != "You are a helpful assistant.":
            prompt = system_prompt + "\n\n" + prompt

        conversation = [{"role": "system", "content": prompt}]
        trace = []
        tool_calls = []

        for iterations in range(max_iterations):
            from app.nodes.llm_node import _sync_chat_completion
            try:
                response = _sync_chat_completion(messages=conversation, model=model, temperature=temperature, max_tokens=4096)
            except Exception as e:
                return {"final_answer": f"[Error] {e}", "tool_calls": tool_calls, "iterations": iterations + 1, "trace": trace}

            if not response:
                return {"final_answer": "Empty response from LLM", "tool_calls": tool_calls, "iterations": iterations + 1, "trace": trace}

            trace.append({"step": iterations + 1, "type": "llm_response", "content": response})

            # Parse ReAct format
            final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
            if final_match:
                return {"final_answer": final_match.group(1).strip(), "tool_calls": tool_calls, "iterations": iterations + 1, "trace": trace}

            action_match = re.search(r"Action:\s*(\w+)\s*\nAction Input:\s*(.*?)(?:\n|$)", response, re.DOTALL)
            if action_match:
                tool_name = action_match.group(1).strip()
                raw_input = action_match.group(2).strip()
                try:
                    tool_args = json.loads(raw_input)
                except json.JSONDecodeError:
                    tool_args = {"input": raw_input}

                tool_calls.append({"name": tool_name, "arguments": tool_args})
                tool_def = self._find_tool(tool_defs, tool_name)
                if tool_def is None:
                    result = {"error": f"Unknown tool: {tool_name}. Available: {[t.name for t in tool_defs]}"}
                else:
                    try:
                        result = self._execute_tool(tool_def, tool_args, ctx)
                    except Exception as e:
                        result = {"error": str(e)}

                obs = json.dumps({"Observation": result}, ensure_ascii=False)
                conversation.append({"role": "assistant", "content": response})
                conversation.append({"role": "user", "content": obs})
                trace.append({"step": iterations + 1, "type": "observation", "content": result})
            else:
                # No action found — treat response as final answer
                # Strip any prefix like "Thought:" to get clean answer
                thought_match = re.search(r"(?:Thought:|Answer:)\s*(.*)", response, re.DOTALL)
                answer = thought_match.group(1).strip() if thought_match else response
                return {"final_answer": answer, "tool_calls": tool_calls, "iterations": iterations + 1, "trace": trace}

        return {"final_answer": "Max iterations reached.", "tool_calls": tool_calls, "iterations": max_iterations, "trace": trace}

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
