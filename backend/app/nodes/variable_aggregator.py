"""Variable Aggregator node.

Merges outputs from multiple upstream branches into a single dictionary.
Supports flat mode (each source's output placed under its alias key) and
nested mode (same behavior for MVP).
"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class VariableAggregatorNode(BaseNodeExecutor):
    """变量聚合节点：合并多个分支的输出"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        sources = config.get("sources", [])
        result = {}

        for source in sources:
            node_id = source.get("node_id", "")
            alias = source.get("alias", node_id)

            try:
                node_output = ctx.get(node_id)
                result[alias] = node_output
            except KeyError:
                result[alias] = None

        return result
