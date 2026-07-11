"""Tests for HumanInputNodeExecutor — manual review placeholder."""

import pytest
from app.engine.context import ExecutionContext
from app.nodes.human_input import HumanInputNodeExecutor


class TestHumanInputNode:
    def test_returns_waiting_status(self):
        """验证返回等待人工审核状态"""
        executor = HumanInputNodeExecutor()
        ctx = ExecutionContext({})
        config = {
            "prompt": "Please review the document",
            "fields": [{"name": "approved", "type": "boolean"}],
        }

        result = executor.execute(ctx, config)
        assert result["status"] == "waiting_for_input"
        assert result["prompt"] == "Please review the document"
        assert result["approval_required"] is True

    def test_default_prompt(self):
        """验证未指定 prompt 时使用默认值"""
        executor = HumanInputNodeExecutor()
        ctx = ExecutionContext({})
        config = {}

        result = executor.execute(ctx, config)
        assert result["status"] == "waiting_for_input"
        assert "review" in result["prompt"].lower()

    def test_empty_fields(self):
        """验证空 fields 列表"""
        executor = HumanInputNodeExecutor()
        ctx = ExecutionContext({})
        config = {"fields": []}

        result = executor.execute(ctx, config)
        assert result["fields"] == []
