"""Synchronous workflow execution engine.

Orchestrates DAG traversal, node execution via the node registry, and
produces a timeline of SSE events that can be streamed to the client.
"""

from app.engine.dag import WorkflowDag, topological_sort
from app.engine.context import ExecutionContext
from app.engine.sse import SSEEvent
from app.nodes.base import BaseNodeExecutor


class WorkflowExecutor:
    """同步工作流执行引擎

    Walks the DAG in topological order, instantiates node executors
    from a registry, and runs each node sequentially within a level.
    Execution events (start / done / error) are recorded and accessible
    via ``get_events()`` for later SSE streaming.

    Parameters
    ----------
    dag : WorkflowDag
        The DAG to execute.
    node_registry : dict[str, type[BaseNodeExecutor]]
        Mapping from node type string to executor class.
    db : AsyncSession, optional
        Database session for nodes that need data access (e.g. knowledge retrieval).
    tenant_id : any, optional
        Tenant identifier for multi-tenant isolation.
    """

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

    def execute(self, inputs: dict) -> dict:
        """同步执行工作流

        Args:
            inputs: 工作流输入参数字典

        Returns:
            输出节点返回的结果字典（若没有输出节点则返回空字典）

        Raises:
            ValueError: 遇到未知节点类型
        """
        ctx = ExecutionContext(inputs, db=self._db, tenant_id=self._tenant_id)
        self._add_event("workflow_start", {"inputs": inputs})

        try:
            levels = topological_sort(self.dag)
        except ValueError:
            raise

        output_result: dict = {}

        for level in levels:
            for node in level:
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
                except Exception as e:
                    self._add_event("node_error", {"node_id": node["id"], "error": str(e)})
                    raise

                # If this is an output node, capture the result
                if node_type == "output":
                    output_result = result

        self._add_event("workflow_done", {"output": output_result})
        return output_result

    def get_events(self) -> list[dict]:
        """获取执行事件列表

        Returns:
            按时间顺序排列的事件字典列表
        """
        return [e.to_dict() for e in self._events]

    def _add_event(self, event_type: str, data: dict):
        """Record an SSE event."""
        self._events.append(SSEEvent(event_type, data))
