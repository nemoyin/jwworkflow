import React from 'react';
import { NodeProps } from 'reactflow';
import { RocketOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const AgentNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  const tools: Array<{ name?: string }> = config.tools || [];

  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<RocketOutlined />}
      color="#1890ff"
      typeLabel="Agent"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.system_prompt ? (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
            }}
          >
            <strong>系统提示:</strong> {config.system_prompt.substring(0, 40)}
            {config.system_prompt.length > 40 ? '...' : ''}
          </span>
        ) : (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
        {tools.length > 0 && (
          <span>
            <strong>工具:</strong> {tools.map((t) => t.name || '?').join(', ')}
          </span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default AgentNode;
