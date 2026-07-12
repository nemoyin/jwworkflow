import React from 'react';
import { NodeProps } from 'reactflow';
import { MessageOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const AnswerNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper data={data} selected={selected} icon={<MessageOutlined />}
      color="#52c41a" typeLabel="Answer (对话)">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.source && <span><strong>来源:</strong> {config.source}</span>}
        {!config.source && <span style={{ color: '#bbb', fontStyle: 'italic' }}>对话输出节点</span>}
      </div>
    </BaseNodeWrapper>
  );
};
export default AnswerNode;
