import React from 'react';
import { NodeProps } from 'reactflow';
import { ExperimentOutlined } from '@ant-design/icons';
import BaseNodeWrapper, { BaseNodeData } from './BaseNode';

const RuleEngineNode: React.FC<NodeProps<BaseNodeData>> = ({ data, selected }) => {
  const config = data.config || {};
  const rules: Array<{ name?: string; operator?: string; threshold?: any }> = config.rules || [];
  return (
    <BaseNodeWrapper data={data} selected={selected} icon={<ExperimentOutlined />}
      color="#eb2f96" typeLabel="规则引擎">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span><strong>规则数:</strong> {rules.length}</span>
        {rules.length > 0 && (
          <div style={{ fontSize: 10, color: '#888' }}>
            {rules.slice(0, 3).map((r, i) => (
              <div key={i}>{r.name || '未命名'}: {r.operator} {r.threshold}</div>
            ))}
            {rules.length > 3 && <div>...还有 {rules.length - 3} 条</div>}
          </div>
        )}
      </div>
    </BaseNodeWrapper>
  );
};
export default RuleEngineNode;
