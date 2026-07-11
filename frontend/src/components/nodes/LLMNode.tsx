import React from 'react';
import { NodeProps } from 'reactflow';
import {
  ThunderboltOutlined,
  RobotOutlined,
  ApiOutlined,
  FileSearchOutlined,
} from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

type LLMConfig = {
  model?: string;
  prompt?: string;
  temperature?: number;
  max_tokens?: number;
};

const LLMNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = (data.config || {}) as LLMConfig;
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<RobotOutlined />}
      color="#1890ff"
      typeLabel="LLM / Agent"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span>
          <strong>模型:</strong> {config.model || 'gpt-4o'}
        </span>
        {config.temperature !== undefined && (
          <span>
            <strong>温度:</strong> {config.temperature}
          </span>
        )}
        {config.prompt && (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
            }}
          >
            <strong>提示词:</strong> {config.prompt.substring(0, 40)}
            {config.prompt.length > 40 ? '...' : ''}
          </span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default LLMNode;

/**
 * Knowledge Retrieval Node — shares the same blue color as LLM
 */
export const KnowledgeRetrievalNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<FileSearchOutlined />}
      color="#1890ff"
      typeLabel="知识检索"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.knowledge_base && (
          <span><strong>知识库:</strong> {config.knowledge_base}</span>
        )}
        {config.top_k !== undefined && (
          <span><strong>Top-K:</strong> {config.top_k}</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

/**
 * HTTP Request Node — orange colored
 */
export const HttpRequestNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<ApiOutlined />}
      color="#fa8c16"
      typeLabel="HTTP 请求"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.url && (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
            }}
          >
            <strong>URL:</strong> {config.url}
          </span>
        )}
        {config.method && (
          <span><strong>方法:</strong> {config.method.toUpperCase()}</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

/**
 * Human Input Node — purple colored
 */
export const HumanInputNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<ThunderboltOutlined />}
      color="#722ed1"
      typeLabel="人工输入"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.prompt_text && (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
            }}
          >
            <strong>提示:</strong> {config.prompt_text.substring(0, 40)}
          </span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

/**
 * Iteration Node — purple colored
 */
export const IterationNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<ThunderboltOutlined />}
      color="#722ed1"
      typeLabel="迭代"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.iterations !== undefined && (
          <span><strong>迭代次数:</strong> {config.iterations}</span>
        )}
        {config.collection && (
          <span><strong>集合:</strong> {config.collection}</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};
