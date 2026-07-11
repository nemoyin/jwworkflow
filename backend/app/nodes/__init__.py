from app.nodes.base import BaseNodeExecutor
from app.nodes.registry import NODE_REGISTRY, register_node, get_node
from app.nodes.input_node import InputNodeExecutor
from app.nodes.llm_node import LLMNodeExecutor
from app.nodes.template_node import TemplateNodeExecutor
from app.nodes.output_node import OutputNodeExecutor

# 注册所有内置节点
register_node(NODE_REGISTRY, "input", InputNodeExecutor)
register_node(NODE_REGISTRY, "llm", LLMNodeExecutor)
register_node(NODE_REGISTRY, "template", TemplateNodeExecutor)
register_node(NODE_REGISTRY, "output", OutputNodeExecutor)

__all__ = [
    "BaseNodeExecutor", "NODE_REGISTRY", "register_node", "get_node",
    "InputNodeExecutor", "LLMNodeExecutor",
    "TemplateNodeExecutor", "OutputNodeExecutor",
]
