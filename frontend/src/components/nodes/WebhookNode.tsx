import React from 'react';
import { NodeProps } from 'reactflow';
import { ApiOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const WebhookNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  return (
    <BaseNodeWrapper data={data} selected={selected} icon={<ApiOutlined />}
      color="#52c41a" typeLabel="Webhook">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {config.secret && <span><strong>签名:</strong> 已配置</span>}
        <span style={{ fontSize: 11, color: '#888' }}>HTTP 触发入口</span>
      </div>
    </BaseNodeWrapper>
  );
};
export default WebhookNode;
