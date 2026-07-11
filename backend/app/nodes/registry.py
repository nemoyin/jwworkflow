from app.nodes.base import BaseNodeExecutor


NODE_REGISTRY: dict[str, type[BaseNodeExecutor]] = {}


def register_node(
    registry: dict[str, type[BaseNodeExecutor]],
    node_type: str,
    executor_cls: type[BaseNodeExecutor],
):
    """注册节点执行器到指定注册表"""
    registry[node_type] = executor_cls


def get_node(
    registry: dict[str, type[BaseNodeExecutor]],
    node_type: str,
) -> type[BaseNodeExecutor] | None:
    """从注册表获取节点执行器类"""
    return registry.get(node_type)
