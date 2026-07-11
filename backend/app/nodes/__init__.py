from app.nodes.base import BaseNodeExecutor
from app.nodes.registry import NODE_REGISTRY, register_node, get_node
from app.nodes.input_node import InputNodeExecutor
from app.nodes.llm_node import LLMNodeExecutor
from app.nodes.template_node import TemplateNodeExecutor
from app.nodes.output_node import OutputNodeExecutor
from app.nodes.if_else import IfElseNodeExecutor
from app.nodes.iteration import IterationNodeExecutor
from app.nodes.variable_aggregator import VariableAggregatorNode
from app.nodes.code_executor import CodeNodeExecutor
from app.nodes.http_request import HttpRequestNodeExecutor
from app.nodes.doc_extractor import DocExtractorNodeExecutor
from app.nodes.human_input import HumanInputNodeExecutor
from app.nodes.knowledge_node import KnowledgeRetrievalNodeExecutor

# 注册所有内置节点
register_node(NODE_REGISTRY, "input", InputNodeExecutor)
register_node(NODE_REGISTRY, "llm", LLMNodeExecutor)
register_node(NODE_REGISTRY, "template", TemplateNodeExecutor)
register_node(NODE_REGISTRY, "output", OutputNodeExecutor)
register_node(NODE_REGISTRY, "if-else", IfElseNodeExecutor)
register_node(NODE_REGISTRY, "iteration", IterationNodeExecutor)
register_node(NODE_REGISTRY, "variable-aggregator", VariableAggregatorNode)
register_node(NODE_REGISTRY, "code", CodeNodeExecutor)
register_node(NODE_REGISTRY, "http-request", HttpRequestNodeExecutor)
register_node(NODE_REGISTRY, "doc-extractor", DocExtractorNodeExecutor)
register_node(NODE_REGISTRY, "human-input", HumanInputNodeExecutor)
register_node(NODE_REGISTRY, "knowledge-retrieval", KnowledgeRetrievalNodeExecutor)

__all__ = [
    "BaseNodeExecutor", "NODE_REGISTRY", "register_node", "get_node",
    "InputNodeExecutor", "LLMNodeExecutor",
    "TemplateNodeExecutor", "OutputNodeExecutor",
    "IfElseNodeExecutor", "IterationNodeExecutor", "VariableAggregatorNode",
    "CodeNodeExecutor", "HttpRequestNodeExecutor",
    "DocExtractorNodeExecutor", "HumanInputNodeExecutor",
    "KnowledgeRetrievalNodeExecutor",
]
