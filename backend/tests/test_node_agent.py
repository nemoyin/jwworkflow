"""Tests for AgentNodeExecutor — LLM-driven tool selection and execution.

MVP phase uses a stub LLM that consumes a configurable tool-call sequence
(``_stub_tool_calls``).  These tests exercise the full execution flow:
prompt building, tool look-up, HTTP execution, code execution, error
handling, and max-iterations termination.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.engine.context import ExecutionContext
from app.nodes.agent_node import AgentNodeExecutor
from app.schemas.tool import ToolDefinition


class TestAgentNode:
    # ------------------------------------------------------------------
    # Basic / default behavior
    # ------------------------------------------------------------------

    def test_default_stub_returns_final_answer_immediately(self):
        """无 _stub_tool_calls 时直接返回 final_answer"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({"query": "hello"})
        config = {
            "system_prompt": "You are a helpful assistant.",
            "model": "gpt-4",
        }
        result = executor.execute(ctx, config)
        assert "final_answer" in result
        assert "gpt-4" in result["final_answer"]
        assert result["tool_calls"] == []
        assert result["iterations"] == 1

    def test_default_max_iterations_constant(self):
        """验证 DEFAULT_MAX_ITERATIONS = 5"""
        assert AgentNodeExecutor.DEFAULT_MAX_ITERATIONS == 5

    def test_empty_config_uses_defaults(self):
        """空 config 也能正常工作（使用所有默认值）"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        result = executor.execute(ctx, {})
        assert result["final_answer"]
        assert result["iterations"] == 1

    # ------------------------------------------------------------------
    # Tool call flow
    # ------------------------------------------------------------------

    def test_single_tool_call_then_final_answer(self):
        """单次工具调用后返回 final_answer"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        tool_def = ToolDefinition(
            name="echo",
            description="Echo back the input",
            endpoint="code",
            input_schema={"code": "result = {'echo': message}"},
        )
        config = {
            "system_prompt": "You are a helpful assistant.",
            "tools": [tool_def.model_dump()],
            "model": "gpt-4",
            "_stub_tool_calls": [
                {"name": "echo", "arguments": {"message": "hello", "code": "result = {'echo': message}"}},
            ],
        }
        result = executor.execute(ctx, config)
        assert "final_answer" in result
        assert result["iterations"] == 2  # 1 tool call + 1 final answer
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "echo"

    def test_multiple_tool_calls(self):
        """多次工具调用后再返回 final_answer"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        tools = [
            ToolDefinition(name="add", description="Add two numbers", endpoint="code"),
            ToolDefinition(name="multiply", description="Multiply two numbers", endpoint="code"),
        ]
        config = {
            "system_prompt": "Calculator agent.",
            "tools": [t.model_dump() for t in tools],
            "max_iterations": 10,
            "_stub_tool_calls": [
                {"name": "add", "arguments": {"a": 1, "b": 2, "code": "result = {'sum': a + b}"}},
                {"name": "multiply", "arguments": {"x": 3, "y": 4, "code": "result = {'product': x * y}"}},
            ],
        }
        result = executor.execute(ctx, config)
        assert result["iterations"] == 3  # 2 tool calls + 1 final
        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["name"] == "add"
        assert result["tool_calls"][1]["name"] == "multiply"

    # ------------------------------------------------------------------
    # Max iterations
    # ------------------------------------------------------------------

    def test_max_iterations_stops_loop(self):
        """达到 max_iterations 时停止并返回提示"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        tool_def = ToolDefinition(
            name="loop_tool",
            description="A tool that never ends",
            endpoint="code",
        )
        # _stub_tool_calls longer than max_iterations, starts with 1 tool call
        config = {
            "max_iterations": 3,
            "_stub_tool_calls": [
                {"name": "loop_tool", "arguments": {"code": "result = {'ok': True}"}},
                {"name": "loop_tool", "arguments": {"code": "result = {'ok': True}"}},
                {"name": "loop_tool", "arguments": {"code": "result = {'ok': True}"}},
                {"name": "loop_tool", "arguments": {"code": "result = {'ok': True}"}},
            ],
            "tools": [tool_def.model_dump()],
        }
        result = executor.execute(ctx, config)
        # max_iterations=3, so 3 tool calls consume all iterations, no final answer
        assert result["iterations"] == 3
        assert "Max iterations reached" in result["final_answer"]

    # ------------------------------------------------------------------
    # Unknown tool
    # ------------------------------------------------------------------

    def test_unknown_tool_returns_error(self):
        """工具不存在时返回错误信息"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        config = {
            "system_prompt": "Agent.",
            "tools": [
                {"name": "valid_tool", "description": "A valid tool", "endpoint": "code"},
            ],
            "_stub_tool_calls": [
                {"name": "nonexistent_tool", "arguments": {}},
            ],
        }
        result = executor.execute(ctx, config)
        # The tool call error is fed back to LLM, then final answer
        assert result["iterations"] >= 1
        # The tool_call should be recorded
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "nonexistent_tool"

    # ------------------------------------------------------------------
    # HTTP tool execution
    # ------------------------------------------------------------------

    def test_http_tool_get_request(self):
        """验证 HTTP GET 工具调用"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"result": "data"}
        mock_response.text = '{"result": "data"}'

        tool_def = ToolDefinition(
            name="search",
            description="Search API",
            endpoint="https://api.example.com/search",
            method="GET",
        )

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "system_prompt": "Search agent.",
                "tools": [tool_def.model_dump()],
                "_stub_tool_calls": [
                    {"name": "search", "arguments": {"params": {"q": "hello"}}},
                ],
            }
            result = executor.execute(ctx, config)

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "search"

        # Verify request was made correctly
        mock_client.request.assert_called_once()
        call_args, call_kwargs = mock_client.request.call_args
        assert call_kwargs.get("url") == "https://api.example.com/search"
        assert call_kwargs.get("method") == "GET"

    def test_http_tool_post_with_body(self):
        """验证 HTTP POST 工具调用"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"id": 42}
        mock_response.text = '{"id": 42}'

        tool_def = ToolDefinition(
            name="create_item",
            description="Create an item",
            endpoint="https://api.example.com/items",
            method="POST",
        )

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "system_prompt": "Create item agent.",
                "tools": [tool_def.model_dump()],
                "_stub_tool_calls": [
                    {
                        "name": "create_item",
                        "arguments": {
                            "body": {"name": "test", "price": 100},
                            "headers": {"X-API-Key": "secret"},
                        },
                    },
                ],
            }
            result = executor.execute(ctx, config)

        assert len(result["tool_calls"]) == 1
        mock_client.request.assert_called_once()
        _, kwargs = mock_client.request.call_args
        assert kwargs.get("json") == {"name": "test", "price": 100}
        assert kwargs["headers"]["X-API-Key"] == "secret"

    def test_http_tool_timeout(self):
        """验证 HTTP 超时返回错误"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        tool_def = ToolDefinition(
            name="slow_api",
            description="Slow API",
            endpoint="https://api.example.com/slow",
            method="GET",
        )

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.side_effect = httpx.TimeoutException(
                "timeout", request=None
            )

            config = {
                "system_prompt": "Agent.",
                "tools": [tool_def.model_dump()],
                "_stub_tool_calls": [
                    {"name": "slow_api", "arguments": {}},
                ],
            }
            result = executor.execute(ctx, config)

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "slow_api"

    def test_http_tool_connection_error(self):
        """验证 HTTP 连接错误返回错误信息"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        tool_def = ToolDefinition(
            name="bad_api",
            description="Bad API",
            endpoint="https://api.example.com/bad",
            method="GET",
        )

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.side_effect = httpx.ConnectError(
                "Connection refused", request=None
            )

            config = {
                "system_prompt": "Agent.",
                "tools": [tool_def.model_dump()],
                "_stub_tool_calls": [
                    {"name": "bad_api", "arguments": {}},
                ],
            }
            result = executor.execute(ctx, config)

        assert len(result["tool_calls"]) == 1

    # ------------------------------------------------------------------
    # Code tool execution
    # ------------------------------------------------------------------

    def test_code_tool_basic(self):
        """验证代码型工具基本执行"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        config = {
            "system_prompt": "Code agent.",
            "tools": [
                {
                    "name": "compute",
                    "description": "Run computation",
                    "endpoint": "code",
                },
            ],
            "_stub_tool_calls": [
                {
                    "name": "compute",
                    "arguments": {
                        "x": 5,
                        "y": 3,
                        "code": "result = {'sum': x + y, 'product': x * y}",
                    },
                },
            ],
        }
        result = executor.execute(ctx, config)
        assert result["iterations"] >= 1
        assert result["tool_calls"][0]["name"] == "compute"

    def test_code_tool_missing_code_key(self):
        """代码型工具缺少 code 参数时返回错误"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        config = {
            "system_prompt": "Agent.",
            "tools": [
                {"name": "bad", "description": "Missing code", "endpoint": "code"},
            ],
            "_stub_tool_calls": [
                {"name": "bad", "arguments": {}},
            ],
        }
        result = executor.execute(ctx, config)
        # Should still complete with a tool_call recorded
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "bad"

    def test_code_tool_syntax_error(self):
        """代码型工具语法错误返回错误"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})

        config = {
            "system_prompt": "Agent.",
            "tools": [
                {"name": "broken", "description": "Broken code", "endpoint": "code"},
            ],
            "_stub_tool_calls": [
                {
                    "name": "broken",
                    "arguments": {"code": "result = {"},  # invalid syntax
                },
            ],
        }
        result = executor.execute(ctx, config)
        assert len(result["tool_calls"]) == 1

    # ------------------------------------------------------------------
    # ToolDefinition schema
    # ------------------------------------------------------------------

    def test_tool_definition_defaults(self):
        """验证 ToolDefinition 默认值"""
        td = ToolDefinition(name="test", description="Test tool", endpoint="http://example.com")
        assert td.method == "GET"
        assert td.input_schema == {}

    def test_tool_definition_with_all_fields(self):
        """验证 ToolDefinition 全部字段"""
        td = ToolDefinition(
            name="search",
            description="Search engine",
            endpoint="https://api.example.com/search",
            method="POST",
            input_schema={"query": {"type": "string"}},
        )
        assert td.name == "search"
        assert td.method == "POST"
        assert td.input_schema == {"query": {"type": "string"}}

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def test_build_prompt_with_tools(self):
        """验证工具描述被正确添加到 system prompt"""
        tools = [
            ToolDefinition(name="tool_a", description="Tool A", endpoint="code"),
            ToolDefinition(name="tool_b", description="Tool B", endpoint="http://example.com"),
        ]
        prompt = AgentNodeExecutor._build_prompt("You are an agent.", tools)
        assert "You are an agent." in prompt
        assert "tool_a" in prompt
        assert "Tool A" in prompt
        assert "tool_b" in prompt
        assert "Tool B" in prompt
        assert "Available tools:" in prompt

    def test_build_prompt_without_tools(self):
        """无工具时返回原样"""
        prompt = AgentNodeExecutor._build_prompt("Hello.", [])
        assert prompt == "Hello."

    # ------------------------------------------------------------------
    # Tool parsing
    # ------------------------------------------------------------------

    def test_parse_tools_from_dicts(self):
        """验证从字典列表解析 ToolDefinition"""
        tools = AgentNodeExecutor._parse_tools([
            {"name": "a", "description": "A", "endpoint": "code"},
            {"name": "b", "description": "B", "endpoint": "http://example.com", "method": "POST"},
        ])
        assert len(tools) == 2
        assert all(isinstance(t, ToolDefinition) for t in tools)
        assert tools[0].name == "a"
        assert tools[1].method == "POST"

    def test_parse_tools_from_objects(self):
        """验证直接传入 ToolDefinition 对象"""
        td = ToolDefinition(name="x", description="X", endpoint="code")
        tools = AgentNodeExecutor._parse_tools([td])
        assert len(tools) == 1
        assert tools[0] is td

    def test_parse_tools_invalid_type(self):
        """非法类型抛出 TypeError"""
        with pytest.raises(TypeError):
            AgentNodeExecutor._parse_tools(["not_a_tool"])

    # ------------------------------------------------------------------
    # Tool finding
    # ------------------------------------------------------------------

    def test_find_tool_found(self):
        """验证能找到存在的工具"""
        tools = [
            ToolDefinition(name="alpha", description="Alpha", endpoint="code"),
            ToolDefinition(name="beta", description="Beta", endpoint="code"),
        ]
        found = AgentNodeExecutor._find_tool(tools, "alpha")
        assert found is not None
        assert found.name == "alpha"

    def test_find_tool_not_found(self):
        """不存在的工具返回 None"""
        tools = [ToolDefinition(name="only_one", description="Only", endpoint="code")]
        found = AgentNodeExecutor._find_tool(tools, "nope")
        assert found is None

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_custom_max_iterations(self):
        """验证自定义 max_iterations 生效"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        config = {
            "max_iterations": 1,
        }
        result = executor.execute(ctx, config)
        assert result["iterations"] == 1

    def test_iterations_count_matches_tool_calls(self):
        """迭代次数正确反映工具调用次数"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        tool_calls_stub = [
            {"name": "t1", "arguments": {"code": "result = {'ok': 1}"}},
            {"name": "t2", "arguments": {"code": "result = {'ok': 2}"}},
            {"name": "t3", "arguments": {"code": "result = {'ok': 3}"}},
        ]
        config = {
            "tools": [
                {"name": "t1", "description": "T1", "endpoint": "code"},
                {"name": "t2", "description": "T2", "endpoint": "code"},
                {"name": "t3", "description": "T3", "endpoint": "code"},
            ],
            "max_iterations": 10,
            "_stub_tool_calls": tool_calls_stub,
        }
        result = executor.execute(ctx, config)
        # 3 tool calls + 1 final answer = 4 iterations
        assert result["iterations"] == 4
        assert len(result["tool_calls"]) == 3

    def test_empty_tool_calls_list(self):
        """空列表的 _stub_tool_calls 等同于 immediate final answer"""
        executor = AgentNodeExecutor()
        ctx = ExecutionContext({})
        config = {
            "_stub_tool_calls": [],
        }
        result = executor.execute(ctx, config)
        assert result["iterations"] == 1
        assert result["tool_calls"] == []
