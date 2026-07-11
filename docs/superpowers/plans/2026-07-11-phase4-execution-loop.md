# Phase 4: 完整执行闭环 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development

**Goal:** 实现完整的工作流闭环——画布拖拽 → 保存 → 执行 → SSE 实时展示结果。新增控制流节点（If-Else/Iteration）和数据处理节点（Code/HTTP/DocExtractor/HumanInput）。

**Architecture:** 后端新增节点执行器，前端新增 SSE 集成。扩展节点注册表。

## Global Constraints

- 项目根目录：`D:\AI\opc\jwworkflow`
- TDD（后端），TypeScript（前端）

---

### Task 1: 控制流节点（If-Else + Iteration）

**Files:**
- Create: `backend/app/nodes/if_else.py`
- Create: `backend/app/nodes/iteration.py`
- Create: `backend/app/nodes/variable_aggregator.py`
- Create: `backend/tests/test_node_if_else.py`
- Create: `backend/tests/test_node_iteration.py`
- Modify: `backend/app/nodes/__init__.py`

- [ ] **Step 1: 实现 If-Else 节点**

```python
# backend/app/nodes/if_else.py
class IfElseNodeExecutor(BaseNodeExecutor):
    """条件分支节点：根据条件表达式选择执行路径"""
    
    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        conditions = config.get("conditions", [])
        for cond in conditions:
            variable = cond.get("variable", "")
            operator = cond.get("operator", "eq")
            value = cond.get("value")
            
            # 解析变量值
            resolved = ctx.resolve_variable(variable) if "{{" in str(variable) else variable
            
            # 比较操作
            match operator:
                case "eq": result = resolved == value
                case "ne": result = resolved != value
                case "gt": result = float(resolved) > float(value)
                case "gte": result = float(resolved) >= float(value)
                case "lt": result = float(resolved) < float(value)
                case "lte": result = float(resolved) <= float(value)
                case "contains": result = value in str(resolved)
                case "is_empty": result = not resolved
                case _: result = False
            
            if result:
                return {"selected_branch": cond.get("branch", "default"), "matched": True}
        
        return {"selected_branch": "default", "matched": False}
```

- [ ] **Step 2: 实现 Iteration 节点**
- [ ] **Step 3: 实现 VariableAggregator**
- [ ] **Step 4: 测试 + 提交**

---

### Task 2: 数据处理节点（Code + HTTP + DocExtractor + HumanInput）

**Files:**
- Create: `backend/app/nodes/code_executor.py`
- Create: `backend/app/nodes/http_request.py`
- Create: `backend/app/nodes/doc_extractor.py`
- Create: `backend/app/nodes/human_input.py`
- Create: `backend/tests/test_node_code.py`
- Create: `backend/tests/test_node_http.py`
- Create: `backend/tests/test_node_doc.py`
- Modify: `backend/app/nodes/__init__.py`

- [ ] **Step 1: 实现 Code 节点（Python 沙箱）**
- [ ] **Step 2: 实现 HTTP 请求节点**
- [ ] **Step 3: 实现文档提取器节点**
- [ ] **Step 4: 测试 + 提交**

---

### Task 3: 前端执行闭环集成

**Files:**
- Modify: `frontend/src/pages/WorkflowEditorPage.tsx` (添加运行按钮+结果面板)
- Modify: `frontend/src/stores/workflowStore.ts` (SSE 集成)

- [ ] **Step 1: 前端运行按钮 + 执行流程**
- [ ] **Step 2: SSE 实时节点高亮集成**
- [ ] **Step 3: 前端节点配置面板扩展（支持所有节点类型）**
- [ ] **Step 4: 提交**

---

### Task 4: 运行历史 API + 前端

**Files:**
- Create: `backend/app/api/runs.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/pages/RunHistoryPage.tsx`

**Interfaces:** `GET /api/runs` — 运行历史列表；`GET /api/runs/:id` — 运行详情（含节点结果快照）

- [ ] **Step 1: 后端运行历史 API**
- [ ] **Step 2: 前端运行历史页面**
- [ ] **Step 3: 提交**

---

## Phase 4 验证

```bash
cd /d/AI/opc/jwworkflow/backend && JWT_SECRET=test-secret pytest tests/ -v
# Expected: 70+ tests all pass
```
