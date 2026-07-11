import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Tag } from 'antd';

export interface BaseNodeData {
  label: string;
  config: Record<string, any>;
  [key: string]: any;
}

interface BaseNodeWrapperProps {
  children: React.ReactNode;
  data: BaseNodeData;
  selected: boolean;
  icon: React.ReactNode;
  color: string;
  typeLabel: string;
  showHandles?: boolean;
}

const BaseNodeWrapper: React.FC<BaseNodeWrapperProps> = ({
  children,
  selected,
  icon,
  color,
  typeLabel,
  showHandles = true,
}) => {
  return (
    <div
      style={{
        background: '#fff',
        border: `1px solid ${selected ? color : '#d9d9d9'}`,
        borderRadius: 8,
        borderLeft: `4px solid ${color}`,
        padding: 0,
        minWidth: 180,
        maxWidth: 260,
        boxShadow: selected
          ? `0 0 0 2px ${color}33, 0 2px 8px rgba(0,0,0,0.08)`
          : '0 1px 4px rgba(0,0,0,0.04)',
        transition: 'box-shadow 0.2s, border-color 0.2s',
        cursor: 'pointer',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {showHandles && (
        <>
          <Handle
            type="target"
            position={Position.Top}
            style={{
              width: 10,
              height: 10,
              border: `2px solid ${color}`,
              background: '#fff',
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            style={{
              width: 10,
              height: 10,
              border: `2px solid ${color}`,
              background: '#fff',
            }}
          />
        </>
      )}

      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 12px 4px',
        }}
      >
        <span style={{ color, fontSize: 16, display: 'flex', alignItems: 'center' }}>
          {icon}
        </span>
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {typeLabel}
        </span>
        <Tag color={color} style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0, border: 'none' }}>
          {typeLabel}
        </Tag>
      </div>

      {/* Body */}
      <div style={{ padding: '4px 12px 10px', fontSize: 12, color: '#666' }}>
        {children}
      </div>
    </div>
  );
};

export default BaseNodeWrapper;

/**
 * Helper: create a typed React Flow node component
 */
export function createNodeComponent<P extends Record<string, any> = {}>(
  renderFn: React.FC<NodeProps<BaseNodeData & P>>
): React.FC<NodeProps<BaseNodeData & P>> {
  return renderFn;
}
