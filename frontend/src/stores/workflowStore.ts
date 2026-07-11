import { create } from 'zustand';
import { Node, Edge, applyNodeChanges, applyEdgeChanges, Connection, addEdge } from 'reactflow';
import { api } from '../services/api';

interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  workflowId: string | null;
  workflowName: string;

  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: Connection) => void;
  addNode: (type: string, position: { x: number; y: number }) => void;
  selectNode: (node: Node | null) => void;
  updateNodeConfig: (nodeId: string, config: any) => void;
  loadWorkflow: (id: string) => Promise<void>;
  saveWorkflow: () => Promise<void>;
  executeWorkflow: (inputs: any) => Promise<any>;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  workflowId: null,
  workflowName: '',

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
    const res: any = await api.post(`/workflows/${workflowId}/run`, inputs);
    return res.result;
  },
}));
