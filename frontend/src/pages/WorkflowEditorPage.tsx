import { useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import { message } from 'antd';
import { useWorkflowStore } from '../stores/workflowStore';
import { useSSE } from '../hooks/useSSE';
import CanvasToolbar from '../components/canvas/CanvasToolbar';
import NodePalette from '../components/canvas/NodePalette';
import WorkflowCanvas from '../components/canvas/WorkflowCanvas';
import ExecutionOverlay from '../components/canvas/ExecutionOverlay';
import NodeConfigPanel from '../components/panels/NodeConfigPanel';
import RunResultPanel from '../components/panels/RunResultPanel';
import { nodeTypes } from '../components/nodes';

const WorkflowEditorPage = () => {
  const { id } = useParams<{ id: string }>();
  const workflowId = useWorkflowStore((s) => s.workflowId);
  const loadWorkflow = useWorkflowStore((s) => s.loadWorkflow);
  const executionStatus = useWorkflowStore((s) => s.executionStatus);

  // Execution actions from store
  const setNodeExecutionState = useWorkflowStore((s) => s.setNodeExecutionState);
  const setExecutionStatus = useWorkflowStore((s) => s.setExecutionStatus);
  const setExecutionFinalOutput = useWorkflowStore((s) => s.setExecutionFinalOutput);

  // Load workflow on mount
  useEffect(() => {
    if (id) {
      loadWorkflow(id).catch(() => {
        message.error('加载工作流失败');
      });
    }
  }, [id, loadWorkflow]);

  // SSE event handlers
  const handleNodeStart = useCallback(
    (data: { node_id: string; node_type: string }) => {
      setNodeExecutionState(data.node_id, 'running');
    },
    [setNodeExecutionState]
  );

  const handleNodeDone = useCallback(
    (data: { node_id: string; output: unknown }) => {
      setNodeExecutionState(data.node_id, 'completed', data.output);
    },
    [setNodeExecutionState]
  );

  const handleNodeError = useCallback(
    (data: { node_id: string; error: string }) => {
      setNodeExecutionState(data.node_id, 'error', undefined, data.error);
    },
    [setNodeExecutionState]
  );

  const handleWorkflowDone = useCallback(
    (data: { output: unknown; error?: string; status?: string }) => {
      if (data.status === 'error' || data.error) {
        setExecutionStatus('error');
        message.error(data.error || '工作流执行失败');
      } else {
        setExecutionStatus('completed');
        message.success('工作流执行完成');
      }
      setExecutionFinalOutput(data.output ?? data.error ?? null);
    },
    [setExecutionStatus, setExecutionFinalOutput]
  );

  // Connect SSE when execution is running
  useSSE(workflowId, {
    enabled: executionStatus === 'running',
    onEvent: {
      node_start: handleNodeStart,
      node_done: handleNodeDone,
      node_error: handleNodeError,
      workflow_done: handleWorkflowDone,
    },
  });

  return (
    <ReactFlowProvider>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          width: '100%',
          overflow: 'hidden',
        }}
      >
        <CanvasToolbar />
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <NodePalette />
          <div style={{ flex: 1, position: 'relative' }}>
            <WorkflowCanvas nodeTypes={nodeTypes} />
            <ExecutionOverlay />
          </div>
          <NodeConfigPanel />
          <RunResultPanel />
        </div>
      </div>
    </ReactFlowProvider>
  );
};

export default WorkflowEditorPage;
