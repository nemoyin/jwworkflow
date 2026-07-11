import React from 'react';
import { NodeProps } from 'reactflow';
import { FileSearchOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const DocExtractorNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper
      data={data}
      selected={selected}
      icon={<FileSearchOutlined />}
      color="#fa8c16"
      typeLabel="文档提取"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.file_type && (
          <span><strong>格式:</strong> {config.file_type.toUpperCase()}</span>
        )}
        {config.file_path && (
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 220,
            }}
          >
            <strong>路径:</strong> {config.file_path}
          </span>
        )}
        {!config.file_type && !config.file_path && (
          <span style={{ color: '#bbb', fontStyle: 'italic' }}>等待配置...</span>
        )}
      </div>
    </BaseNodeWrapper>
  );
};

export default DocExtractorNode;
