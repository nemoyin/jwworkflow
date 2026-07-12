import React, { useCallback } from 'react';
import { Button, Space, message, Tooltip, Dropdown } from 'antd';
import {
  ZoomInOutlined, ZoomOutOutlined, AimOutlined, SaveOutlined,
  PlayCircleOutlined, BugOutlined, EyeOutlined, LinkOutlined,
  DownOutlined,
} from '@ant-design/icons';
import { useReactFlow } from 'reactflow';
import { useNavigate } from 'react-router-dom';
import { useWorkflowStore } from '../../stores/workflowStore';

const CanvasToolbar: React.FC = () => {
  const reactFlowInstance = useReactFlow();
  const navigate = useNavigate();
  const { saveWorkflow, executeWorkflow, workflowName, executionStatus, workflowId } =
    useWorkflowStore();
  const isRunning = executionStatus === 'running';

  const handleZoomIn = useCallback(() => reactFlowInstance.zoomIn(), [reactFlowInstance]);
  const handleZoomOut = useCallback(() => reactFlowInstance.zoomOut(), [reactFlowInstance]);
  const handleFitView = useCallback(() => reactFlowInstance.fitView(), [reactFlowInstance]);

  const handleSave = useCallback(async () => {
    try {
      await saveWorkflow();
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
  }, [saveWorkflow]);

  const handleRun = useCallback(async () => {
    if (isRunning) return;
    try {
      await executeWorkflow({});
    } catch (err: unknown) {
      message.error((err as Error).message || '执行失败');
    }
  }, [executeWorkflow, isRunning]);

  const handleDebug = useCallback(async () => {
    if (!workflowId) {
      message.warning('请先保存工作流');
      return;
    }
    try {
      await executeWorkflow({ _debug: true });
      message.success('调试执行完成');
    } catch (err: unknown) {
      message.error((err as Error).message || '调试失败');
    }
  }, [executeWorkflow, workflowId]);

  const previewItems = [
    { key: 'preview', icon: <EyeOutlined />, label: '预览页面', onClick: () => workflowId && navigate(`/preview/${workflowId}`) },
    { key: 'webhook', icon: <LinkOutlined />, label: 'Webhook URL',
      onClick: () => {
        if (!workflowId) { message.warning('请先保存工作流'); return; }
        const url = `${window.location.origin}/api/webhooks/trigger/${workflowId}`;
        navigator.clipboard.writeText(url).then(() => message.success('Webhook URL 已复制')).catch(() => message.info(url));
      }
    },
  ];

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', borderBottom: '1px solid #f0f0f0', background: '#fff' }}>
      <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>
        {workflowName || '工作流编辑器'}
      </span>
      <Space wrap>
        <Button icon={<SaveOutlined />} onClick={handleSave}>保存</Button>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRun} loading={isRunning}>
          {isRunning ? '运行中...' : '运行'}
        </Button>
        <Tooltip title="调试模式（单步追踪）">
          <Button icon={<BugOutlined />} onClick={handleDebug} disabled={!workflowId}>调试</Button>
        </Tooltip>
        <Dropdown menu={{ items: previewItems }} trigger={['click']}>
          <Button icon={<EyeOutlined />}>
            发布 <DownOutlined />
          </Button>
        </Dropdown>
        <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
        <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
        <Button icon={<AimOutlined />} onClick={handleFitView} />
      </Space>
    </div>
  );
};

export default CanvasToolbar;
