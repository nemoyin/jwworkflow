# Phase 7: 多模型管理 Implementation Plan

**Goal:** 实现多 LLM 模型管理——支持多个供应商（DeepSeek/OpenAI/Ollama 等）、模型注册表、健康检查、节点下拉选择。

---

### Task 1: 数据库模型 + API

**Files:**
- Create: `backend/app/models/model_provider.py` — ModelProvider ORM
- Create: `backend/app/models/model_registry.py` — ModelRegistry ORM
- Create: `backend/app/schemas/model_management.py` — Pydantic schemas
- Create: `backend/app/api/models.py` — CRUD API + 健康检查
- Create: `backend/tests/test_api_models.py` — 测试

**ModelProvider:**
- id, tenant_id, name, provider_type (deepseek/openai/ollama/azure/anthropic), api_key, base_url, is_active, sort_order, created_at

**ModelRegistry:**
- id, provider_id, model_name, display_name, capabilities JSONB (tool_calls, streaming, max_tokens, max_input_tokens), is_active, sort_order, created_at

**预置种子数据：**
- Provider: DeepSeek (api.deepseek.com)
  - deepseek-v4-pro, deepseek-v4-chat, deepseek-chat
- Provider: OpenAI (api.openai.com)
  - gpt-4o, gpt-4o-mini, gpt-4-turbo
- Provider: Ollama (localhost:11434)
  - 本地模型按需添加

---

### Task 2: LLM 服务多 Provider 支持

**Modify:**
- `backend/app/services/llm_service.py` — 按 provider 动态创建客户端
- `backend/app/nodes/llm_node.py` — 从 registry 获取模型列表
- `backend/app/nodes/agent_node.py` — 从 registry 获取模型列表
- `backend/app/config.py` — 保留默认 LLM 配置作为 fallback

---

### Task 3: 前端模型管理页面

**Files:**
- Create: `frontend/src/pages/ModelManagementPage.tsx`
- Modify: `frontend/src/components/panels/NodeConfigPanel.tsx` — 模型下拉从 registry 获取

---

## 依赖

- Phase 1 基础设施（数据库/路由/认证）
- 开发周期：~1 天
