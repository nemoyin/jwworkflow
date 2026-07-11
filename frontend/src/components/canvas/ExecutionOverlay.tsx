import React from 'react';
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { useWorkflowStore } from '../../stores/workflowStore';

/**
 * CSS keyframes for the blue pulsing animation on running nodes.
 * Injected globally via a <style> tag when execution is active.
 */
const pulseKeyframes = `
@keyframes node-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.6), 0 0 0 3px rgba(24, 144, 255, 0.3);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(24, 144, 255, 0.2), 0 0 0 6px rgba(24, 144, 255, 0.15);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0), 0 0 0 3px rgba(24, 144, 255, 0.3);
  }
}
`;

/**
 * ExecutionOverlay injects CSS keyframes for node highlighting
 * and shows a floating "executing..." status badge during workflow execution.
 */
const ExecutionOverlay: React.FC = () => {
  const executionStatus = useWorkflowStore((s) => s.executionStatus);

  if (executionStatus !== 'running') return null;

  return (
    <>
      <style>{pulseKeyframes}</style>
      <div
        style={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(255,255,255,0.95)',
          padding: '8px 16px',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          pointerEvents: 'none',
        }}
      >
        <Spin
          indicator={
            <LoadingOutlined style={{ fontSize: 18, color: '#1890ff' }} spin />
          }
        />
        <span style={{ fontSize: 13, color: '#1890ff', fontWeight: 500 }}>
          执行中...
        </span>
      </div>
    </>
  );
};

export default ExecutionOverlay;
