import type { NodeTypes } from 'reactflow';
import LLMNode, {
  KnowledgeRetrievalNode,
  HttpRequestNode,
  HumanInputNode,
  IterationNode,
} from './LLMNode';
import InputNode from './InputNode';
import TemplateNode from './TemplateNode';
import OutputNode from './OutputNode';
import IfElseNode from './IfElseNode';
import CodeNode from './CodeNode';
import VariableAggregatorNode from './VariableAggregatorNode';
import AgentNode from './AgentNode';
import DocExtractorNode from './DocExtractorNode';
import RuleEngineNode from './RuleEngineNode';
import AnswerNode from './AnswerNode';
import WebhookNode from './WebhookNode';

export {
  LLMNode,
  InputNode,
  TemplateNode,
  OutputNode,
  IfElseNode,
  CodeNode,
  KnowledgeRetrievalNode,
  HttpRequestNode,
  HumanInputNode,
  IterationNode,
  VariableAggregatorNode,
  AgentNode,
};

/**
 * React Flow nodeTypes mapping.
 * Register all custom node components here so React Flow can render them
 * by the `type` string stored on each node.
 */
export const nodeTypes: NodeTypes = {
  input: InputNode,
  llm: LLMNode,
  template: TemplateNode,
  code: CodeNode,
  output: OutputNode,
  ifelse: IfElseNode,
  // Extended node types
  'knowledge-retrieval': KnowledgeRetrievalNode,
  'http-request': HttpRequestNode,
  'human-input': HumanInputNode,
  iteration: IterationNode,
  'doc-extractor': DocExtractorNode,
  'variable-aggregator': VariableAggregatorNode,
  agent: AgentNode,
  'rule-engine': RuleEngineNode,
  answer: AnswerNode,
  webhook: WebhookNode,
  'excel-parser': InputNode,
};

/**
 * Color map for node categories (used by NodeConfigPanel and NodePalette)
 */
export const nodeColorMap: Record<string, string> = {
  input: '#52c41a',
  llm: '#1890ff',
  'knowledge-retrieval': '#1890ff',
  agent: '#1890ff',
  template: '#fa8c16',
  code: '#fa8c16',
  'http-request': '#fa8c16',
  'doc-extractor': '#fa8c16',
  'variable-aggregator': '#fa8c16',
  output: '#52c41a',
  ifelse: '#722ed1',
  iteration: '#722ed1',
  'human-input': '#722ed1',
  'rule-engine': '#eb2f96',
  answer: '#52c41a',
  webhook: '#52c41a',
  'excel-parser': '#fa8c16',
};

/**
 * Human-readable labels for node types
 */
export const nodeLabelMap: Record<string, string> = {
  input: '输入',
  llm: 'LLM 调用',
  'knowledge-retrieval': '知识检索',
  agent: 'Agent 代理',
  template: '模板渲染',
  code: '代码执行',
  'http-request': 'HTTP 请求',
  'doc-extractor': '文档提取',
  'variable-aggregator': '变量聚合',
  output: '输出',
  ifelse: '条件分支',
  iteration: '迭代',
  'human-input': '人工输入',
  'rule-engine': '规则引擎',
  answer: 'Answer',
  webhook: 'Webhook',
  'excel-parser': 'Excel解析',
};
