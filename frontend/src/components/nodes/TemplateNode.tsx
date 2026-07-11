import React from 'react';
import { NodeProps } from 'reactflow';
import { FileTextOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const TemplateNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<FileTextOutlined />}
      color="#fa8c16"
      typeLabel="模板渲染"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.template && (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
            }}
          >
            <strong>模板:</strong> {config.template.substring(0, 50)}
            {config.template.length > 50 ? '...' : ''}
          </span>
        )}
        {!config.template && (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default TemplateNode;
