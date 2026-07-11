import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import { message } from 'antd';
import { useWorkflowStore } from '../stores/workflowStore';
import CanvasToolbar from '../components/canvas/CanvasToolbar';
import NodePalette from '../components/canvas/NodePalette';
import WorkflowCanvas from '../components/canvas/WorkflowCanvas';

const WorkflowEditorPage = () => {
  const { id } = useParams<{ id: string }>();
  const loadWorkflow = useWorkflowStore((s) => s.loadWorkflow);

  useEffect(() => {
    if (id) {
      loadWorkflow(id).catch(() => {
        message.error('加载工作流失败');
      });
    }
  }, [id, loadWorkflow]);

  return (
    <ReactFlowProvider>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          width: '100vw',
        }}
      >
        <CanvasToolbar />
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <NodePalette />
          <div style={{ flex: 1, position: 'relative' }}>
            <WorkflowCanvas />
          </div>
        </div>
      </div>
    </ReactFlowProvider>
  );
};

export default WorkflowEditorPage;
