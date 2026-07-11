import { create } from 'zustand';
import { Node, Edge, applyNodeChanges, applyEdgeChanges, Connection, addEdge } from 'reactflow';
import { api } from '../services/api';

export type ExecutionStatus = 'idle' | 'running' | 'completed' | 'error';
export type ExecutionNodeState = 'pending' | 'running' | 'completed' | 'error';

interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  workflowId: string | null;
  workflowName: string;

  // Execution state
  executionStatus: ExecutionStatus;
  nodeExecutionStates: Record<string, ExecutionNodeState>;
  executionNodeResults: Record<string, unknown>;
  executionErrors: Record<string, string>;
  executionFinalOutput: unknown;

  // Node/edge actions
  onNodesChange: (changes: any[]) => void;
  onEdgesChange: (changes: any[]) => void;
  onConnect: (connection: Connection) => void;
  addNode: (type: string, position: { x: number; y: number }) => void;
  selectNode: (node: Node | null) => void;
  updateNodeConfig: (nodeId: string, config: Record<string, any>) => void;
  loadWorkflow: (id: string) => Promise<void>;
  saveWorkflow: () => Promise<void>;
  executeWorkflow: (inputs: Record<string, any>) => Promise<void>;

  // Execution actions
  setExecutionStatus: (status: ExecutionStatus) => void;
  setNodeExecutionState: (
    nodeId: string,
    state: ExecutionNodeState,
    output?: unknown,
    error?: string
  ) => void;
  setExecutionFinalOutput: (output: unknown) => void;
  resetExecution: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  workflowId: null,
  workflowName: '',

  // Initial execution state
  executionStatus: 'idle',
  nodeExecutionStates: {},
  executionNodeResults: {},
  executionErrors: {},
  executionFinalOutput: null,

  // --- Node/edge actions ---

  onNodesChange: (changes) => set({ nodes: applyNodeChanges(changes, get().nodes) }),

  onEdgesChange: (changes) => set({ edges: applyEdgeChanges(changes, get().edges) }),

  onConnect: (connection) => set({ edges: addEdge(connection, get().edges) }),

  addNode: (type, position) => {
    const id = `node_${Date.now()}`;
    const newNode: Node = {
      id,
      type,
      position,
      data: { label: type, config: {} },
    };
    set({ nodes: [...get().nodes, newNode] });
  },

  selectNode: (node) => set({ selectedNode: node }),

  updateNodeConfig: (nodeId, config) => {
    set({
      nodes: get().nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, config } } : n
      ),
    });
  },

  loadWorkflow: async (id) => {
    const wf: any = await api.get(`/workflows/${id}`);
    set({
      workflowId: wf.id,
      workflowName: wf.name,
      nodes: wf.dag_definition.nodes || [],
      edges: wf.dag_definition.edges || [],
    });
  },

  saveWorkflow: async () => {
    const state = get();
    const dag = { nodes: state.nodes, edges: state.edges };
    if (state.workflowId) {
      await api.put(`/workflows/${state.workflowId}`, { dag_definition: dag });
    } else {
      const res: any = await api.post('/workflows', {
        name: '新建工作流',
        dag_definition: dag,
      });
      set({ workflowId: res.id, workflowName: res.name });
    }
  },

  executeWorkflow: async (inputs) => {
    const { workflowId } = get();
    if (!workflowId) throw new Error('请先保存工作流');

    // Reset execution state and mark as running
    set({
      executionStatus: 'running',
      nodeExecutionStates: {},
      executionNodeResults: {},
      executionErrors: {},
      executionFinalOutput: null,
      // Clear execution state from node data
      nodes: get().nodes.map((n) => {
        const { executionState: _es, ...restData } = n.data as Record<string, any>;
        return { ...n, data: restData };
      }),
    });

    try {
      // POST to trigger backend execution; SSE stream will pick up events
      const resp: any = await api.post(`/workflows/${workflowId}/run`, inputs);
      // If the response already contains output (synchronous completion), use it
      if (resp && resp.output !== undefined) {
        set({ executionFinalOutput: resp.output });
      }
      if (resp && resp.status === 'error') {
        set({ executionStatus: 'error', executionFinalOutput: resp.error || '执行失败' });
      }
    } catch (err: unknown) {
      const errorMessage = (err as Error).message || '执行失败';
      set({
        executionStatus: 'error',
        executionErrors: { __workflow__: errorMessage },
      });
      throw err;
    }
  },

  // --- Execution actions ---

  setExecutionStatus: (status) => set({ executionStatus: status }),

  setNodeExecutionState: (nodeId, state, output, error) => {
    set((prev) => {
      // Update the node's data so React Flow re-renders it with execution state
      const updatedNodes = prev.nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, executionState: state } }
          : n
      );

      const patch: Partial<WorkflowState> = {
        nodes: updatedNodes,
        nodeExecutionStates: {
          ...prev.nodeExecutionStates,
          [nodeId]: state,
        },
      };

      if (output !== undefined) {
        patch.executionNodeResults = {
          ...prev.executionNodeResults,
          [nodeId]: output,
        };
      }

      if (error !== undefined) {
        patch.executionErrors = {
          ...prev.executionErrors,
          [nodeId]: error,
        };
      }

      return patch;
    });
  },

  setExecutionFinalOutput: (output) => set({ executionFinalOutput: output }),

  resetExecution: () => {
    set((prev) => ({
      executionStatus: 'idle',
      nodeExecutionStates: {},
      executionNodeResults: {},
      executionErrors: {},
      executionFinalOutput: null,
      // Remove execution state from node data
      nodes: prev.nodes.map((n) => {
        const { executionState: _es, ...restData } = n.data as Record<string, any>;
        return { ...n, data: restData };
      }),
    }));
  },
}));
