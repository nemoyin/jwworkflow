import React from 'react';
import { NodeProps } from 'reactflow';
import { CodeOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const CodeNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<CodeOutlined />}
      color="#fa8c16"
      typeLabel="代码执行"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.language ? (
          <span><strong>语言:</strong> {config.language}</span>
        ) : (
          <span><strong>语言:</strong> Python</span>
        )}
        {config.code && (
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
            <strong>代码:</strong> {config.code.substring(0, 40).replace(/\n/g, ' ')}
            {config.code.length > 40 ? '...' : ''}
          </span>
        )}
        {!config.code && (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default CodeNode;
