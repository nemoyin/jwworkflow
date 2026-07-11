"""Iteration / Loop node.

Iterates over an array from the execution context and executes sub-nodes
for each item. Each item is set in the context under the configured
item variable name so that sub-nodes can reference it via template syntax.
"""

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class IterationNodeExecutor(BaseNodeExecutor):
    """循环节点：迭代数组并对每个元素执行子节点"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        items_source = config.get("items_source", "")
        item_variable = config.get("item_variable", "current_item")
        sub_nodes = config.get("sub_nodes", [])

        # Resolve the items array from context
        if "{{" in str(items_source):
            items = ctx.resolve_variable(items_source)
        else:
            items = ctx.resolve_variable("{{ " + items_source + " }}")

        if not isinstance(items, list):
            raise TypeError(
                f"Iteration source must be a list, got {type(items).__name__}"
            )

        # Store original value of item_variable if it exists
        original_item_value = None
        if hasattr(ctx, item_variable):
            try:
                original_item_value = ctx.inputs.get(item_variable)
            except (KeyError, AttributeError):
                pass

        results = []
        for index, item in enumerate(items):
            # Set current item in the context inputs so sub-nodes can reference it
            ctx._inputs[item_variable] = item

            # Execute sub-nodes for this item
            sub_results = {}
            for sub_node in sub_nodes:
                # Sub-nodes can be different types — resolve the executor from registry
                # For MVP, we handle template sub-nodes inline
                sub_type = sub_node.get("type", "")
                sub_config = sub_node.get("config", {})

                if sub_type == "template":
                    rendered = ctx.resolve_variable(sub_config.get("template", ""))
                    sub_results["output"] = rendered
                    sub_results["index"] = index
                else:
                    # For other types, pass through the config as result
                    sub_results = {"index": index, "sub_type": sub_type}

            if sub_results:
                results.append(sub_results)
            else:
                results.append(item)

        # Restore original value
        if original_item_value is not None:
            ctx._inputs[item_variable] = original_item_value
        elif item_variable in ctx._inputs:
            del ctx._inputs[item_variable]

        return {
            "iteration_count": len(results),
            "results": results,
        }
