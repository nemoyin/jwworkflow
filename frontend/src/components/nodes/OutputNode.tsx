import React from 'react';
import { NodeProps } from 'reactflow';
import { ArrowDownOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const OutputNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<ArrowDownOutlined />}
      color="#52c41a"
      typeLabel="输出"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.output_type && (
          <span><strong>输出类型:</strong> {config.output_type}</span>
        )}
        {config.file_name && (
          <span><strong>文件名:</strong> {config.file_name}</span>
        )}
        {!config.output_type && !config.file_name && (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default OutputNode;
