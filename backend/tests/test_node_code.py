"""Tests for CodeNodeExecutor — sandboxed Python code execution."""

import pytest
from app.engine.context import ExecutionContext
from app.nodes.code_executor import CodeNodeExecutor


class TestCodeNode:
    def test_basic_code_execution(self):
        """验证基本 Python 代码执行"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({"x": 10})
        config = {
            "code": "result = {'output': ctx.inputs['x'] * 2}"
        }
        result = executor.execute(ctx, config)
        assert result == {"output": 20}

    def test_code_returns_dict(self):
        """验证代码可直接返回字典"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {
            "code": "result = {'message': 'hello', 'count': 42}"
        }
        result = executor.execute(ctx, config)
        assert result == {"message": "hello", "count": 42}

    def test_code_can_access_config(self):
        """验证代码可以访问 config 参数"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {"multiplier": 3, "code": "result = {'value': config['multiplier'] * 7}"}
        result = executor.execute(ctx, config)
        assert result == {"value": 21}

    def test_empty_code_returns_empty_output(self):
        """验证空代码返回空输出"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {"code": ""}
        result = executor.execute(ctx, config)
        assert result == {"output": ""}

    def test_code_syntax_error_returns_error(self):
        """验证语法错误返回错误信息"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {"code": "result = {"}  # invalid syntax
        result = executor.execute(ctx, config)
        assert "error" in result
        assert result["success"] is False

    def test_code_runtime_error_returns_error(self):
        """验证运行时错误返回错误信息"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {"code": "result = 1 / 0"}
        result = executor.execute(ctx, config)
        assert "error" in result
        assert result["success"] is False

    def test_code_can_use_builtins(self):
        """验证代码可以使用允许的内置函数"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({"items": [3, 1, 2]})
        config = {
            "code": (
                "result = {"
                "'sorted': sorted(ctx.inputs['items']), "
                "'total': sum(ctx.inputs['items'])"
                "}"
            )
        }
        result = executor.execute(ctx, config)
        assert result == {"sorted": [1, 2, 3], "total": 6}

    def test_code_cannot_use_dangerous_builtins(self):
        """验证危险内置函数被限制（open 等不可用）"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {"code": "result = open('/etc/passwd')"}
        result = executor.execute(ctx, config)
        assert "error" in result

    def test_code_result_is_non_dict_value(self):
        """验证非 dict 的 result 被包装为 {'output': result}"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({})
        config = {"code": "result = 'hello world'"}
        result = executor.execute(ctx, config)
        assert result == {"output": "hello world"}

    def test_node_output_can_be_accessed(self):
        """验证代码可以访问其他节点的输出"""
        executor = CodeNodeExecutor()
        ctx = ExecutionContext({"prefix": "Result: "})
        ctx.set("n1", {"value": 42})
        config = {
            "code": (
                "val = ctx.get('n1')['value']\n"
                "result = {'output': ctx.inputs['prefix'] + str(val)}"
            )
        }
        result = executor.execute(ctx, config)
        assert result == {"output": "Result: 42"}
