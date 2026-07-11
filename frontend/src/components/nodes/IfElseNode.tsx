import React from 'react';
import { NodeProps } from 'reactflow';
import { BranchesOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const IfElseNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<BranchesOutlined />}
      color="#722ed1"
      typeLabel="条件分支"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.condition && (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
              fontFamily: 'monospace',
              fontSize: 11,
            }}
          >
            <strong>条件:</strong> {config.condition.substring(0, 50)}
            {config.condition.length > 50 ? '...' : ''}
          </span>
        )}
        {!config.condition && (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default IfElseNode;
