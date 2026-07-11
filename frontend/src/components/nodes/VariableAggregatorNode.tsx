import React from 'react';
import { NodeProps } from 'reactflow';
import { ApartmentOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const VariableAggregatorNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  const sources: Array<{ node_id?: string; alias?: string }> = config.sources || [];

  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<ApartmentOutlined />}
      color="#fa8c16"
      typeLabel="变量聚合"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {sources.length > 0 ? (
          <span>
            <strong>分支数:</strong> {sources.length}
          </span>
        ) : (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
        {sources.length > 0 && (
          <div style={{ fontSize: 10, color: '#888' }}>
            {sources.map((s, i) => (
              <span key={i}>
                [{s.alias || s.node_id || '?'}]{i < sources.length - 1 ? ', ' : ''}
              </span>
            ))}
          </div>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default VariableAggregatorNode;
