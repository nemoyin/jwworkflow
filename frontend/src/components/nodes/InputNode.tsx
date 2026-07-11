import React from 'react';
import { NodeProps } from 'reactflow';
import { ArrowUpOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const InputNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<ArrowUpOutlined />}
      color="#52c41a"
      typeLabel="输入"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.variable_name && (
          <span><strong>变量名:</strong> {config.variable_name}</span>
        )}
        {config.input_type && (
          <span><strong>类型:</strong> {config.input_type}</span>
        )}
        {!config.variable_name && !config.input_type && (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default InputNode;
