# Phase 6: Agent + 场景接入 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development

**Goal:** 实现 Agent 节点（工具调用）、Chatflow（多轮对话）、工作流模板功能，接入已有场景智能体。

**Architecture:** Agent 节点通过 LLM 推理选择工具，工具通过 HTTP/Code 节点封装。Chatflow 在 Workflow 基础上增加会话变量持久化。

---

### Task 1: Agent 节点

**Files:**
- Create: `backend/app/nodes/agent_node.py`
- Create: `backend/app/nodes/tool_node.py`
- Create: `backend/app/schemas/tool.py`
- Modify: `backend/app/nodes/__init__.py`
- Create: `backend/tests/test_node_agent.py`

**Agent 流程:** 接收输入 → LLM 推理 → 选择工具 → 调用工具 → 返回结果

- [ ] **Step 1: 工具定义 Schema + 内置工具（HTTP 调用封装）**
- [ ] **Step 2: Agent 节点实现（LLM 循环 + 工具选择）**
- [ ] **Step 3: 测试 + 提交**

---

### Task 2: Chatflow 多轮对话支持

**Files:**
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/api/conversations.py`
- Modify: `backend/app/engine/context.py` (会话变量持久化)
- Create: `backend/tests/test_conversations.py`

**Chatflow 与 Workflow 区别:** 会话变量跨轮持久化，支持多轮对话历史

- [ ] **Step 1: Conversation ORM 模型 + 迁移**
- [ ] **Step 2: Chatflow 执行端点（保留对话历史到 ExecutionContext）**
- [ ] **Step 3: 前端聊天 UI 组件**
- [ ] **Step 4: 测试 + 提交**

---

### Task 3: 已有场景智能体适配

**Files:**
- Create: `backend/app/agents/` (场景智能体目录)
- Create: `backend/app/agents/base_agent.py`
- Create: `backend/app/agents/compliance_agent.py` (招标合规)
- Create: `backend/app/agents/collusion_agent.py` (围串标)
- Create: `backend/app/agents/interview_agent.py` (纪检谈话)

- [ ] **Step 1: 场景智能体基类**
- [ ] **Step 2: 适配已有智能体（作为自定义工具注册）**
- [ ] **Step 3: 测试 + 提交**

---

### Task 4: 工作流模板

**Files:**
- Create: `backend/app/models/template.py`
- Create: `backend/app/api/templates.py`
- Create: `frontend/src/pages/TemplateMarketPage.tsx`

- [ ] **Step 1: 模板模型 + 预置模板（合规审查/围串标分析/信访）**
- [ ] **Step 2: 模板市场 API + 前端页面**
- [ ] **Step 3: 从模板创建工作流**
- [ ] **Step 4: 提交**

---

## Phase 6 验证

```bash
cd /d/AI/opc/jwworkflow/backend && JWT_SECRET=test-secret pytest tests/ -v
# Expected: 100+ tests
docker compose up -d
# 浏览器打开 http://localhost:5173 验证全流程
```
