# Phase 5: 知识库 + RAG Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development

**Goal:** 实现文档上传 → 解析（PDF/DOCX/TXT）→ 分块 → Embedding → pgvector 存储 → 混合检索的完整 RAG 管道。

**Architecture:** 后端 `services/rag_service.py` 管理完整管道，`api/knowledge.py` 提供文档 CRUD，`/api/knowledge/upload` 上传接口。Knowledge Retrieval 节点调用 RAG 服务。

**Tech Stack:** Python (PyPDF2, python-docx), pgvector, sentence-transformers / OpenAI embeddings

## Global Constraints

- TDD for all backend
- Git Bash on Windows

---

### Task 1: 文档管理 API

**Files:**
- Create: `backend/app/api/knowledge.py`
- Create: `backend/app/schemas/knowledge.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_api_knowledge.py`

**API:** `POST /api/knowledge/upload` (multipart), `GET /api/knowledge`, `DELETE /api/knowledge/:id`

- [ ] **Step 1: 文档 ORM 模型 + 迁移**
- [ ] **Step 2: 文档上传 API（保存到 /data/uploads）**
- [ ] **Step 3: 文档列表 + 删除 API**
- [ ] **Step 4: 测试 + 提交**

---

### Task 2: RAG 服务（解析→分块→嵌入）

**Files:**
- Create: `backend/app/services/rag_service.py`
- Create: `backend/tests/test_rag.py`

- [ ] **Step 1: 文档解析（PDF/DOCX/TXT）**
- [ ] **Step 2: 文本分块（按段落/Token 大小分割）**
- [ ] **Step 3: Embedding 调用 + pgvector 存储**
- [ ] **Step 4: 混合检索（向量+全文）**
- [ ] **Step 5: 测试 + 提交**

---

### Task 3: 知识检索节点

**Files:**
- Create: `backend/app/nodes/knowledge_node.py`
- Modify: `backend/app/nodes/__init__.py`
- Create: `backend/tests/test_node_knowledge.py`

- [ ] **Step 1: 实现 KnowledgeRetrievalNode**
- [ ] **Step 2: 注册到 NODE_REGISTRY**
- [ ] **Step 3: 测试 + 提交**

---

### Task 4: 前端知识库管理页面

**Files:**
- Create: `frontend/src/pages/KnowledgePage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 文档上传 UI（拖拽/选择文件）**
- [ ] **Step 2: 文档列表 + 状态展示**
- [ ] **Step 3: 提交**

---

## Phase 5 验证

```bash
cd /d/AI/opc/jwworkflow/backend && JWT_SECRET=test-secret pytest tests/ -v
# Expected: 85+ tests
```
