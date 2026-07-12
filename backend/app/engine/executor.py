"""Workflow execution engine with parallel node execution.

Walks the DAG in topological order. Nodes in the same topological level
are executed concurrently via ThreadPoolExecutor.
"""

from __future__ import annotations

import concurrent.futures as cf
from typing import Any

from app.engine.dag import WorkflowDag, topological_sort
from app.engine.context import ExecutionContext
from app.engine.sse import SSEEvent
from app.nodes.base import BaseNodeExecutor


class WorkflowExecutor:
    """工作流执行引擎（同层节点并行执行）"""

    def __init__(
        self,
        dag: WorkflowDag,
        node_registry: dict[str, type[BaseNodeExecutor]],
        db=None,
        tenant_id=None,
    ):
        self.dag = dag
        self.node_registry = node_registry
        self._db = db
        self._tenant_id = tenant_id
        self._events: list[SSEEvent] = []

    def execute(self, inputs: dict, context: ExecutionContext = None) -> dict:
        ctx = context or ExecutionContext(inputs, db=self._db, tenant_id=self._tenant_id)
        self._add_event("workflow_start", {"inputs": inputs})
        levels = topological_sort(self.dag)
        output_result: dict = {}

        for level in levels:
            if len(level) > 1:
                # Parallel: run all nodes in this level concurrently
                with cf.ThreadPoolExecutor(max_workers=min(len(level), 8)) as pool:
                    fut_map: dict[cf.Future[Any], dict] = {
                        pool.submit(self._run_node, node, ctx): node for node in level
                    }
                    for future in cf.as_completed(fut_map):
                        node = fut_map[future]
                        result = future.result()
                        if node["type"] == "output":
                            output_result = result
            else:
                for node in level:
                    result = self._run_node(node, ctx)
                    if node["type"] == "output":
                        output_result = result

        self._add_event("workflow_done", {"output": output_result})
        return output_result

    def _run_node(self, node: dict, ctx: ExecutionContext) -> Any:
        node_type = node["type"]
        executor_cls = self.node_registry.get(node_type)
        if executor_cls is None:
            raise ValueError(f"Unknown node type: {node_type}")
        executor = executor_cls()
        config = node.get("config", {})
        self._add_event("node_start", {"node_id": node["id"], "node_type": node_type})
        try:
            result = executor.execute(ctx, config)
            ctx.set(node["id"], result)
            self._add_event("node_done", {"node_id": node["id"], "output": result})
            return result
        except Exception as e:
            self._add_event("node_error", {"node_id": node["id"], "error": str(e)})
            raise

    def get_events(self) -> list[dict]:
        return [e.to_dict() for e in self._events]

    def _add_event(self, event_type: str, data: dict):
        self._events.append(SSEEvent(event_type, data))
