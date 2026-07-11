"""Tests for WorkflowExecutor — the synchronous DAG execution engine."""

import pytest
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY


class TestWorkflowExecutor:
    def test_linear_execution(self):
        """验证线性工作流完整执行"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "query", "type": "text"}]}},
                {"id": "n2", "type": "template", "config": {"template": "Hello {{ input.query }}"}},
                {"id": "n3", "type": "output", "config": {"variables": [{"name": "greeting", "source": "n2.output"}]}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        result = executor.execute({"query": "World"})
        assert result == {"greeting": "Hello World"}

    def test_execution_returns_all_node_outputs(self):
        """验证执行返回所有节点输出"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "x", "type": "text"}]}},
                {"id": "n2", "type": "output", "config": {"variables": [{"name": "val", "source": "n1.x"}]}},
            ],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        result = executor.execute({"x": "42"})
        assert result == {"val": "42"}

    def test_unknown_node_type_raises_error(self):
        """验证未知节点类型抛出异常"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "nonexistent", "config": {}},
                {"id": "n2", "type": "output", "config": {"variables": []}},
            ],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        with pytest.raises(ValueError, match="Unknown node type"):
            executor.execute({})

    def test_events_recorded_during_execution(self):
        """验证执行过程中记录事件"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": []}},
                {"id": "n2", "type": "output", "config": {"variables": []}},
            ],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        executor.execute({})
        events = executor.get_events()
        assert len(events) >= 4  # workflow_start, node_start x2, node_done x2, workflow_done
        assert events[0]["type"] == "workflow_start"
        assert events[-1]["type"] == "workflow_done"

    def test_node_error_records_event_and_raises(self):
        """验证节点执行失败时记录事件并抛出异常"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "x", "type": "text"}]}},
                # template node references a non-existent variable to trigger error
                {"id": "n2", "type": "template", "config": {"template": "{{ nonexistent.field }}"}},
                {"id": "n3", "type": "output", "config": {"variables": []}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        with pytest.raises(KeyError):
            executor.execute({"x": "42"})
        events = executor.get_events()
        # Should have workflow_start, node_start(n1), node_done(n1), node_start(n2), node_error(n2)
        error_events = [e for e in events if e["type"] == "node_error"]
        assert len(error_events) == 1
        assert error_events[0]["data"]["node_id"] == "n2"

    def test_empty_dag_returns_empty_output(self):
        """验证空 DAG 返回空结果"""
        dag = WorkflowDag(nodes=[], edges=[])
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        result = executor.execute({})
        assert result == {}

    def test_multiple_parallel_nodes(self):
        """验证并行节点执行"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "a", "type": "text"}, {"name": "b", "type": "text"}]}},
                {"id": "n2", "type": "template", "config": {"template": "A: {{ input.a }}"}},
                {"id": "n3", "type": "template", "config": {"template": "B: {{ input.b }}"}},
                {"id": "n4", "type": "output", "config": {"variables": [{"name": "result_a", "source": "n2.output"}, {"name": "result_b", "source": "n3.output"}]}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n1", "target": "n3"},
                {"id": "e3", "source": "n2", "target": "n4"},
                {"id": "e4", "source": "n3", "target": "n4"},
            ]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        result = executor.execute({"a": "foo", "b": "bar"})
        assert result == {"result_a": "A: foo", "result_b": "B: bar"}
