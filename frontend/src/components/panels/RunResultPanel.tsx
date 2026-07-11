import React, { useEffect, useState } from 'react';
import {
  Drawer,
  Tag,
  Typography,
  List,
  Result,
  Space,
  Button,
  Divider,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useWorkflowStore } from '../../stores/workflowStore';
import { nodeLabelMap } from '../nodes';

const { Text, Paragraph, Title } = Typography;

const executionStatusConfig = {
  idle: { color: 'default' as const, text: '未执行' },
  running: { color: 'processing' as const, text: '执行中' },
  completed: { color: 'success' as const, text: '执行完成' },
  error: { color: 'error' as const, text: '执行出错' },
};

function nodeStateIcon(state: string) {
  switch (state) {
    case 'running':
      return <SyncOutlined spin style={{ color: '#1890ff', fontSize: 14 }} />;
    case 'completed':
      return (
        <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 14 }} />
      );
    case 'error':
      return (
        <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 14 }} />
      );
    default:
      return (
        <ClockCircleOutlined style={{ color: '#d9d9d9', fontSize: 14 }} />
      );
  }
}

function stateText(state: string): string {
  switch (state) {
    case 'running':
      return '运行中';
    case 'completed':
      return '完成';
    case 'error':
      return '出错';
    default:
      return '等待';
  }
}

/**
 * RunResultPanel shows the execution progress and final results
 * in a right-side Ant Design Drawer.
 *
 * - Auto-opens when execution completes or errors
 * - Lists each node with its state/result/error
 * - Shows the final workflow output at the bottom
 */
const RunResultPanel: React.FC = () => {
  const executionStatus = useWorkflowStore((s) => s.executionStatus);
  const executionNodeResults = useWorkflowStore((s) => s.executionNodeResults);
  const executionErrors = useWorkflowStore((s) => s.executionErrors);
  const executionFinalOutput = useWorkflowStore((s) => s.executionFinalOutput);
  const nodes = useWorkflowStore((s) => s.nodes);
  const nodeExecutionStates = useWorkflowStore((s) => s.nodeExecutionStates);
  const resetExecution = useWorkflowStore((s) => s.resetExecution);
  const [open, setOpen] = useState(false);

  // Auto-open drawer when execution completes or errors
  useEffect(() => {
    if (executionStatus === 'completed' || executionStatus === 'error') {
      setOpen(true);
    }
  }, [executionStatus]);

  if (executionStatus === 'idle') return null;

  const statusCfg = executionStatusConfig[executionStatus];

  return (
    <Drawer
      title={
        <Space>
          <span>运行结果</span>
          <Tag color={statusCfg.color}>{statusCfg.text}</Tag>
        </Space>
      }
      placement="right"
      width={420}
      open={open}
      onClose={() => setOpen(false)}
      extra={
        <Button size="small" onClick={resetExecution}>
          清除结果
        </Button>
      }
    >
      {/* Node execution list */}
      <Title level={5} style={{ fontSize: 13, marginBottom: 8 }}>
        节点执行详情
      </Title>
      <List
        size="small"
        dataSource={nodes}
        renderItem={(node) => {
          const state = nodeExecutionStates[node.id] || 'pending';
          const nodeLabel = nodeLabelMap[node.type || ''] || node.type;
          const nodeResult = executionNodeResults[node.id];
          const nodeError = executionErrors[node.id];

          return (
            <List.Item style={{ padding: '8px 0' }}>
              <div style={{ width: '100%' }}>
                <Space style={{ marginBottom: 4 }}>
                  {nodeStateIcon(state)}
                  <Text strong style={{ fontSize: 12 }}>
                    {nodeLabel}
                  </Text>
                  <Tag
                    color={
                      state === 'completed'
                        ? 'success'
                        : state === 'error'
                          ? 'error'
                          : state === 'running'
                            ? 'processing'
                            : 'default'
                    }
                    style={{ fontSize: 10, lineHeight: '16px' }}
                  >
                    {stateText(state)}
                  </Tag>
                </Space>
                {nodeResult != null && state === 'completed' && (
                  <Paragraph
                    ellipsis={{ rows: 2, expandable: true }}
                    style={{
                      fontSize: 11,
                      color: '#666',
                      margin: 0,
                      background: '#f5f5f5',
                      padding: '4px 8px',
                      borderRadius: 4,
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {typeof nodeResult === 'string'
                      ? nodeResult
                      : JSON.stringify(nodeResult, null, 2) || ''}
                  </Paragraph>
                )}
                {nodeError && state === 'error' && (
                  <Paragraph
                    style={{
                      fontSize: 11,
                      color: '#ff4d4f',
                      margin: 0,
                      background: '#fff2f0',
                      padding: '4px 8px',
                      borderRadius: 4,
                      fontFamily: 'monospace',
                    }}
                  >
                    {nodeError}
                  </Paragraph>
                )}
              </div>
            </List.Item>
          );
        }}
      />

      <Divider />

      {/* Final output */}
      <Title level={5} style={{ fontSize: 13, marginBottom: 8 }}>
        最终输出
      </Title>
      {executionStatus === 'completed' && executionFinalOutput != null ? (
        <Paragraph
          style={{
            fontSize: 12,
            background: '#f6ffed',
            padding: 12,
            borderRadius: 4,
            border: '1px solid #b7eb8f',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            maxHeight: 400,
            overflow: 'auto',
          }}
        >
          {typeof executionFinalOutput === 'string'
            ? executionFinalOutput
            : JSON.stringify(executionFinalOutput, null, 2)}
        </Paragraph>
      ) : executionStatus === 'error' ? (
        <Result status="error" title="执行出错" subTitle="请检查节点配置后重试" />
      ) : (
        <Text type="secondary" style={{ fontSize: 12 }}>
          等待执行完成...
        </Text>
      )}
    </Drawer>
  );
};

export default RunResultPanel;
