# Phase 3: 前端画布 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development

**Goal:** 实现 React + React Flow 前端工作流画布——拖拽节点、连接边、配置面板、工作流 CRUD UI、运行结果展示。

**Architecture:** 前端位于 `frontend/`，Vite + React 18 + React Flow + Ant Design + Zustand + TypeScript。

**Tech Stack:** React 18, TypeScript, Vite, React Flow, Ant Design 5, Zustand, EventSource (SSE)

## Global Constraints

- 项目根目录：`D:\AI\opc\jwworkflow`
- Git Bash on Windows
- Conventional Commits

---

### Task 1: 前端脚手架 + API 客户端

**Files:**
- Modify: `frontend/src/App.tsx` (路由配置)
- Create: `frontend/src/services/api.ts` (API 客户端)
- Create: `frontend/src/stores/authStore.ts` (认证状态)
- Create: `frontend/src/pages/LoginPage.tsx`
- Create: `frontend/src/pages/WorkflowListPage.tsx`
- Create: `frontend/src/stores/__init__.ts`

- [ ] **Step 1: 创建 API 客户端**

```typescript
// frontend/src/services/api.ts
const BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) { this.token = token; }
  clearToken() { this.token = null; }

  private async request<T>(method: string, path: string, body?: any): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const res = await fetch(`${BASE_URL}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    if (res.status === 204) return undefined as T;
    return res.json();
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body?: any) { return this.request<T>('POST', path, body); }
  put<T>(path: string, body?: any) { return this.request<T>('PUT', path, body); }
  delete(path: string) { return this.request<void>('DELETE', path); }
}

export const api = new ApiClient();
```

- [ ] **Step 2: 创建认证 Store**

```typescript
// frontend/src/stores/authStore.ts
import { create } from 'zustand';
import { api } from '../services/api';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (tenantName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  isAuthenticated: false,
  login: async (email, password) => {
    const res: any = await api.post('/auth/login', { email, password });
    api.setToken(res.access_token);
    set({ token: res.access_token, isAuthenticated: true });
  },
  register: async (tenantName, email, password) => {
    const res: any = await api.post('/auth/register', { tenant_name: tenantName, email, password });
    api.setToken(res.access_token);
    set({ token: res.access_token, isAuthenticated: true });
  },
  logout: () => {
    api.clearToken();
    set({ token: null, isAuthenticated: false });
  },
}));
```

- [ ] **Step 3: 创建登录页面和路由**
- [ ] **Step 4: Commit**

---

### Task 2: React Flow 画布集成

**Files:**
- Create: `frontend/src/pages/WorkflowEditorPage.tsx`
- Create: `frontend/src/components/canvas/WorkflowCanvas.tsx`
- Create: `frontend/src/components/canvas/CanvasToolbar.tsx`
- Create: `frontend/src/components/canvas/NodePalette.tsx`
- Create: `frontend/src/stores/workflowStore.ts`

**Interfaces:** 画布渲染、拖拽节点、连接边、保存/加载工作流

- [ ] **Step 1: 创建 Workflow Store**

```typescript
// frontend/src/stores/workflowStore.ts
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
  nodes: [], edges: [], selectedNode: null, workflowId: null, workflowName: '',

  onNodesChange: (changes) => set({ nodes: applyNodeChanges(changes, get().nodes) }),
  onEdgesChange: (changes) => set({ edges: applyEdgeChanges(changes, get().edges) }),
  onConnect: (connection) => set({ edges: addEdge(connection, get().edges) }),

  addNode: (type, position) => {
    const id = `node_${Date.now()}`;
    const newNode: Node = {
      id, type, position,
      data: { label: type, config: {} },
    };
    set({ nodes: [...get().nodes, newNode] });
  },

  selectNode: (node) => set({ selectedNode: node }),

  updateNodeConfig: (nodeId, config) => {
    set({
      nodes: get().nodes.map(n => n.id === nodeId ? { ...n, data: { ...n.data, config } } : n),
    });
  },

  loadWorkflow: async (id) => {
    const wf: any = await api.get(`/workflows/${id}`);
    set({
      workflowId: wf.id, workflowName: wf.name,
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
      const res: any = await api.post('/workflows', { name: '新建工作流', dag_definition: dag });
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
```

- [ ] **Step 2: 创建画布组件 (WorkflowCanvas)**
- [ ] **Step 3: 创建节点面板 (NodePalette)**
- [ ] **Step 4: 创建工作流编辑器页面**
- [ ] **Step 5: Commit**

---

### Task 3: 自定义节点 UI 组件

**Files:**
- Create: `frontend/src/components/nodes/LLMNode.tsx`
- Create: `frontend/src/components/nodes/InputNode.tsx`
- Create: `frontend/src/components/nodes/TemplateNode.tsx`
- Create: `frontend/src/components/nodes/OutputNode.tsx`
- Create: `frontend/src/components/nodes/IfElseNode.tsx`
- Create: `frontend/src/components/nodes/CodeNode.tsx`
- Create: `frontend/src/components/nodes/index.ts`
- Create: `frontend/src/components/panels/NodeConfigPanel.tsx`

**Interfaces:** 自定义 React Flow 节点组件 + 节点配置面板

- [ ] **Step 1: 创建节点类型映射和注册**
- [ ] **Step 2: 实现各节点 UI 组件（颜色编码: 蓝=AI,紫=控制,橙=数据,绿=输入/输出）**
- [ ] **Step 3: 创建节点配置面板（点击节点后展开）**
- [ ] **Step 4: Commit**

---

### Task 4: 运行监控 + 结果展示

**Files:**
- Create: `frontend/src/components/panels/RunResultPanel.tsx`
- Create: `frontend/src/hooks/useSSE.ts`
- Create: `frontend/src/components/canvas/ExecutionOverlay.tsx`

**Interfaces:** SSE 实时状态推送、节点高亮动画、运行结果展示

- [ ] **Step 1: 创建 SSE Hook**

```typescript
// frontend/src/hooks/useSSE.ts
import { useEffect, useRef, useCallback } from 'react';

export function useSSE(workflowId: string | null) {
  const esRef = useRef<EventSource | null>(null);
  const callbacksRef = useRef<Record<string, (data: any) => void>>({});

  const on = useCallback((event: string, cb: (data: any) => void) => {
    callbacksRef.current[event] = cb;
  }, []);

  useEffect(() => {
    if (!workflowId) return;
    const es = new EventSource(`/api/workflows/${workflowId}/run/sse`);
    esRef.current = es;

    es.addEventListener('node_start', (e) => callbacksRef.current['node_start']?.(JSON.parse(e.data)));
    es.addEventListener('node_done', (e) => callbacksRef.current['node_done']?.(JSON.parse(e.data)));
    es.addEventListener('node_error', (e) => callbacksRef.current['node_error']?.(JSON.parse(e.data)));
    es.addEventListener('workflow_done', (e) => callbacksRef.current['workflow_done']?.(JSON.parse(e.data)));

    return () => es.close();
  }, [workflowId]);

  return { on };
}
```

- [ ] **Step 2: 创建执行覆盖层（ExecutionOverlay - 节点实时高亮）**
- [ ] **Step 3: 创建运行结果面板**
- [ ] **Step 4: Commit**

---

### Task 5: 权限控制 + 路由守卫

**Files:**
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/AuthGuard.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 实现 AuthGuard 和路由守卫**
- [ ] **Step 2: 实现 AppLayout（侧边栏+顶栏）**
- [ ] **Step 3: Commit**

---

## Phase 3 验证

```bash
cd /d/AI/opc/jwworkflow/frontend
npm install && npm run build
```
Expected: Build succeeds, no TypeScript errors
