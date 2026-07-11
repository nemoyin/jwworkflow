import React, { useCallback } from 'react';
import { Button, Space, message } from 'antd';
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  AimOutlined,
  SaveOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { useReactFlow } from 'reactflow';
import { useWorkflowStore } from '../../stores/workflowStore';

const CanvasToolbar: React.FC = () => {
  const reactFlowInstance = useReactFlow();
  const { saveWorkflow, executeWorkflow, workflowName } = useWorkflowStore();

  const handleZoomIn = useCallback(() => {
    reactFlowInstance.zoomIn();
  }, [reactFlowInstance]);

  const handleZoomOut = useCallback(() => {
    reactFlowInstance.zoomOut();
  }, [reactFlowInstance]);

  const handleFitView = useCallback(() => {
    reactFlowInstance.fitView();
  }, [reactFlowInstance]);

  const handleSave = useCallback(async () => {
    try {
      await saveWorkflow();
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
  }, [saveWorkflow]);

  const handleRun = useCallback(async () => {
    try {
      await executeWorkflow({});
      message.success('执行成功');
    } catch (err: any) {
      message.error(err.message || '执行失败');
    }
  }, [executeWorkflow]);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 16px',
        borderBottom: '1px solid #f0f0f0',
        background: '#fff',
      }}
    >
      <span style={{ fontWeight: 600 }}>{workflowName || '工作流编辑器'}</span>
      <Space>
        <Button icon={<SaveOutlined />} onClick={handleSave}>
          保存
        </Button>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRun}>
          运行
        </Button>
        <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
        <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
        <Button icon={<AimOutlined />} onClick={handleFitView} />
      </Space>
    </div>
  );
};

export default CanvasToolbar;
