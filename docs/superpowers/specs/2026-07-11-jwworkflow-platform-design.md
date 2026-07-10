# jwworkflow: 通用 LLM Agent 工作流编排平台 设计文档

> 日期：2026-07-11
> 状态：设计定稿

---

## 1. 产品定位

### 1.1 愿景

jwworkflow 是一个**面向非技术用户的通用 LLM Agent 工作流编排平台**，通过可视化拖拽搭建 AI 工作流，赋能政企场景的智能化转型。

### 1.2 目标用户

- **一线用户**：业务专家（招标审核员、纪检干部、信访办人员、数据分析师等）
- **能力要求**：零代码，拖拽配置即可搭建 AI 工作流
- **未来扩展**：实施商/ISV 可基于平台定制行业模板后交付给终端客户

### 1.3 目标场景（非 MVP 全部覆盖，但平台可编排支撑）

- 招标文件合规性审查
- 投标书围串标分析
- AI 问数 / 数据分析智能体
- 国企招采采购价智能比对分析
- 纪检模拟谈话智能体
- 12345 投诉舆情分析智能体
- 智慧信访智能体
- 定性量纪辅助 AI 智能体
- 三书比对 AI 智能体

### 1.4 部署模式

- **MVP 阶段**：SaaS 多租户，快速验证
- **远期**：支持私有化部署（政企客户数据安全要求）

---

## 2. 整体架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    🖥️ 前端 (React + React Flow)              │
│   工作流画布 | 节点配置 | 运行监控 | 租户管理                │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST / WebSocket (SSE)
┌───────────────────────▼─────────────────────────────────────┐
│                  🌐 API Gateway (FastAPI)                    │
│    JWT认证 | 多租户路由 | 文件上传                          │
└───┬───────┬───────┬───────┬───────┬────────────────────────-┘
    │       │       │       │       │
    ▼       ▼       ▼       ▼       ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│工作流  │ │Agent  │ │知识库  │ │规则   │ │外部   │
│引擎    │ │运行时  │ │服务    │ │引擎   │ │网关   │
│(DAG)  │ │(场景  │ │(RAG)  │ │(六项  │ │(HTTP) │
│       │ │智能体) │ │       │ │规则)  │ │       │
└──────┘ └──────┘ └──────┘ └──────┘ └──────┘
    │       │       │       │       │
    └───────┴───────┴───────┴───────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  💾 数据层（简化版）                          │
│                                                             │
│  PostgreSQL (唯一重型依赖)                                   │
│     ├─ 用户/租户/工作流定义/运行记录                         │
│     └─ pgvector 扩展 = 内置向量库                            │
│                                                             │
│  本地文件系统（替代 MinIO/S3）                               │
│     ├─ /data/uploads/   上传文档                             │
│     └─ /data/knowledge/ 知识库文件                           │
└────────────────────────────────────────────────────────────-┘
```

### 2.2 架构决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 架构路线 | 全栈自建 | 无许可证顾虑，完全掌控，深度定制 |
| 数据层 | PostgreSQL only + pgvector | 本机一条命令启动，MVP 快速验证 |
| 执行模式 | 同步执行 + SSE 推流 | 简化架构，避免消息队列 |
| 工作流定义 | JSONB 整存 DAG | 灵活快速迭代，无需关系拆表 |
| 文件存储 | 本地文件系统 | MVP 阶段无需对象存储 |

---

## 3. 工作流引擎设计

### 3.1 DAG 定义模型

工作流以 JSON 格式定义，存储在 PostgreSQL 的 `workflows.dag_definition` 字段（JSONB）：

```json
{
  "nodes": [
    { "id": "n1", "type": "input", "config": { "fields": [...] } },
    { "id": "n2", "type": "llm", "config": { "model": "...", "prompt": "..." } },
    { "id": "n3", "type": "knowledge_retrieval", "config": { "knowledge_base": "...", "top_k": 5 } },
    { "id": "n4", "type": "code", "config": { "code": "...", "language": "python" } },
    { "id": "n5", "type": "output", "config": { "variables": [...] } }
  ],
  "edges": [
    { "id": "e1", "source": "n1", "target": "n2", "source_handle": "output", "target_handle": "input" },
    { "id": "e2", "source": "n2", "target": "n3" },
    { "id": "e3", "source": "n3", "target": "n4" },
    { "id": "e4", "source": "n4", "target": "n5" }
  ]
}
```

### 3.2 执行引擎流程（同步 + SSE）

```
1. POST /api/workflows/:id/run → 创建 runs 记录（status=running）
2. 开启 SSE 连接：GET /api/workflows/:id/run/sse
3. 执行流程：
   a. 从 PG 加载 DAG 定义
   b. 初始化 ExecutionContext（含输入变量）
   c. 拓扑排序
   d. 逐层遍历 DAG（同层节点可并行）
   e. 每个节点执行：
      - SSE → node_start
      - 阻塞执行
      - 结果存入上下文
      - SSE → node_done / node_error
   f. 获取输出节点结果
   g. SSE → workflow_done
   h. 持久化运行记录到 runs 表
4. 返回最终结果
```

### 3.3 节点注册表模式

所有节点执行器通过统一接口注册：

```python
class BaseNodeExecutor(ABC):
    """所有节点类型的基类"""
    
    @abstractmethod
    def execute(self, ctx: ExecutionContext, config: dict) -> Any:
        """执行节点逻辑"""
        pass

# 节点注册表
NODE_REGISTRY: dict[str, type[BaseNodeExecutor]] = {}
```

新增节点类型只需继承 `BaseNodeExecutor` + 注册到 `NODE_REGISTRY`。

### 3.4 变量传递与引用

- 引用语法：`{{ node_id.output_field }}`（类似 Jinja2 / Dify 风格）
- 上下文对象 `ExecutionContext`：以 `node_id` 为 key 存储每个节点输出
- 变量聚合器：合并多分支输出为单一可引用变量

### 3.5 错误处理

| 层级 | 策略 |
|------|------|
| 节点级 | 1 次自动重试，超时 60s（LLM 可配置），失败模式：继续/终止/降级 |
| 工作流级 | SSE 推送错误信息，运行记录持久化（即使失败），提供手动重试入口 |

---

## 4. MVP 节点体系（15 种）

### 4.1 入口节点（2种）

| 节点 | 说明 |
|------|------|
| **用户输入** | 定义输入字段：文本/数值/下拉/文件/JSON |
| **Webhook 触发器** | HTTP 回调触发工作流 |

### 4.2 AI/知识节点（3种）

| 节点 | 说明 |
|------|------|
| **LLM** | 多模型推理，提示词编排，流式/非流式输出 |
| **知识检索 (RAG)** | pgvector 向量搜索 + 全文搜索混合检索 |
| **Agent** | 自主推理 + 工具调用，复用已有场景智能体 |

### 4.3 逻辑控制节点（3种）

| 节点 | 说明 |
|------|------|
| **If-Else** | 条件分支：文本/数值/空值判断，IF/ELIF/ELSE 多分支 |
| **迭代 (Iteration)** | 数组元素顺序处理，批量分析场景 |
| **人工输入** | 暂停流程等待人工审核/补充数据 |

### 4.4 数据处理节点（4种）

| 节点 | 说明 |
|------|------|
| **代码 (Code)** | Python 沙箱执行，复杂规则逻辑 |
| **模板 (Template)** | Jinja2 模板渲染，变量插值 |
| **文档提取器** | 解析 PDF/DOCX/TXT |
| **HTTP 请求** | REST API 调用（企查查等外部服务） |

### 4.5 输出节点（2种）

| 节点 | 说明 |
|------|------|
| **Answer（对话流）** | 流式 Markdown 响应 |
| **Output（工作流）** | 结构化多变量输出 |

### 4.6 变量管理（1种）

| 节点 | 说明 |
|------|------|
| **变量聚合器** | 合并多分支输出为单一引用 |

### 4.7 应用类型区分

| 类型 | 执行模式 | 适用场景 |
|------|---------|---------|
| **Workflow** | 无状态、单次运行 | 围串标分析、比价、三书比对 |
| **Chatflow** | 有状态、多轮对话 | 纪检谈话、AI 问数、信访 |

---

## 5. 数据库设计

### 5.1 核心表

#### tenants（租户）
```sql
CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(64) UNIQUE NOT NULL,
    plan        VARCHAR(32) DEFAULT 'free',
    config      JSONB DEFAULT '{}',       -- LLM 密钥等租户级配置
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

#### users（用户）
```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID REFERENCES tenants(id),
    email         VARCHAR(255) UNIQUE NOT NULL,
    role          VARCHAR(32) DEFAULT 'member',  -- admin / member
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);
```

#### workflows（工作流定义，核心表）
```sql
CREATE TABLE workflows (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID REFERENCES tenants(id),
    name          VARCHAR(255) NOT NULL,
    description   TEXT,
    type          VARCHAR(32) DEFAULT 'workflow',  -- workflow | chatflow
    dag_definition JSONB NOT NULL,                 -- 完整 DAG（nodes + edges）
    version       INTEGER DEFAULT 1,
    status        VARCHAR(32) DEFAULT 'draft',     -- draft | published
    created_by    UUID REFERENCES users(id),
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);
```

#### runs（运行记录）
```sql
CREATE TABLE runs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id   UUID REFERENCES workflows(id),
    tenant_id     UUID REFERENCES tenants(id),
    triggered_by  UUID REFERENCES users(id),
    status        VARCHAR(32) DEFAULT 'running',  -- running|success|failed
    input         JSONB,
    output        JSONB,
    error         TEXT,
    duration_ms   INTEGER,
    node_results  JSONB,       -- 每个节点的执行结果快照
    created_at    TIMESTAMPTZ DEFAULT now()
);
```

#### documents（文档/知识库）
```sql
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID REFERENCES tenants(id),
    name        VARCHAR(255) NOT NULL,
    file_path   TEXT NOT NULL,              -- 本地文件路径
    content     TEXT,                        -- 提取后的文本
    chunks      JSONB DEFAULT '[]',         -- 分块列表
    status      VARCHAR(32) DEFAULT 'pending',  -- pending|processing|ready|failed
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

#### embeddings（向量，pgvector 扩展）
```sql
CREATE TABLE embeddings (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id    UUID REFERENCES tenants(id),
    chunk_index  INTEGER,
    chunk_text   TEXT,
    embedding    VECTOR(1536),               -- 嵌入向量
    created_at   TIMESTAMPTZ DEFAULT now()
);
```

### 5.2 多租户隔离策略

- 所有业务表带 `tenant_id` 字段
- API 层从 JWT 自动提取 `tenant_id`
- 查询强制带 `tenant_id` 过滤
- 远期可使用 PostgreSQL Row-Level Security

---

## 6. 前端设计

### 6.1 技术栈

| 组件 | 选型 | 用途 |
|------|------|------|
| 框架 | React 18 | 前端基座 |
| 画布 | React Flow | 工作流 DAG 编辑器 |
| UI 组件 | Ant Design | 管理后台、表单、表格 |
| 状态管理 | Zustand | 轻量级状态管理 |
| 实时通信 | EventSource (SSE) | 工作流执行状态推流 |

### 6.2 主要页面路由

```
/login
/dashboard
/workflows
  ├ /workflows/:id/edit   ← 画布编辑器（核心）
  └ /workflows/:id/runs   ← 运行历史
/knowledge                ← 知识库管理
/runs
/settings
/admin                    ← 租户管理（admin 角色）
```

### 6.3 画布编辑器布局

```
┌──────────────────────────────────────┐
│ ← 返回 │ 工作流名称    │ 发布 │ 运行 │
├──────────┬──────────────────────────-┤
│ 🔍 节点   │                           │
│ ─────────│        画布区域             │
│ 🖱️ 拖拽   │        (React Flow)       │
│          │    ┌────┐    ┌───┐        │
│ 📥 入口   │    │输入│───→│LLM│        │
│ 🤖 AI    │    └────┘    └───┘        │
│ 🔀 控制   │                │          │
│ 📊 数据   │              ┌───┐       │
│ 📤 输出   │              │输出│       │
│          │              └───┘       │
├──────────┴──────────────────────────-┤
│ ⚡ 节点配置面板（点击节点后展开）      │
│   [模型选择] [提示词编辑] [参数设置]   │
└──────────────────────────────────────┘
```

### 6.4 组件架构

```
src/
 ├ components/
 │  ├ canvas/
 │  │  ├ WorkflowCanvas.tsx    # 画布容器
 │  │  ├ CanvasToolbar.tsx     # 工具栏（撤销/重做/缩放）
 │  │  └ NodePalette.tsx       # 左侧节点面板
 │  ├ nodes/                   # 自定义节点（每类一个组件）
 │  │  ├ LLMNode.tsx
 │  │  ├ IfElseNode.tsx
 │  │  ├ KnowledgeNode.tsx
 │  │  ├ CodeNode.tsx
 │  │  ├ AgentNode.tsx
 │  │  ├ HumanInputNode.tsx
 │  │  └ ...
 │  ├ panels/
 │  │  ├ NodeConfigPanel.tsx   # 节点配置面板
 │  │  └ RunResultPanel.tsx    # 运行结果面板
 │  └ layout/
 ├ hooks/                     # useSSE, useWorkflow, useCanvas
 ├ stores/                    # Zustand stores
 ├ pages/                     # 路由页面
 └ services/                  # API 客户端
```

### 6.5 SSE 实时推流

节点执行过程中，前端通过 EventSource 接收实时事件：

| 事件 | 触发时机 | 前端效果 |
|------|---------|---------|
| `node_start` | 节点开始执行 | 节点高亮 + 旋转动画 |
| `node_output` | 节点产生中间输出 | 节点下方显示输出预览 |
| `node_done` | 节点执行成功 | 节点变绿色 ✅ |
| `node_error` | 节点执行失败 | 节点变红色 ❌ |
| `workflow_done` | 工作流完成 | 展示最终结果 |

---

## 7. 后端设计

### 7.1 技术栈

| 组件 | 选型 |
|------|------|
| API 框架 | FastAPI (Python) |
| ORM | SQLAlchemy |
| 迁移 | Alembic |
| 认证 | JWT（PyJWT / python-jose） |
| 向量库 | pgvector (PostgreSQL 扩展) |
| 文档解析 | python-docx / PyPDF2 / Unstructured.io |
| LLM 调用 | litellm / openai SDK（多模型统一接口） |
| 沙箱 | Python 内置 subprocess / restricted Python |

### 7.2 核心 API 路由

```
# 认证
POST /api/auth/register
POST /api/auth/login              → JWT

# 工作流 CRUD
GET    /api/workflows
POST   /api/workflows
GET    /api/workflows/:id
PUT    /api/workflows/:id
DELETE /api/workflows/:id

# 工作流执行
POST /api/workflows/:id/run       # 触发同步执行
GET  /api/workflows/:id/run/sse   # SSE 推流

# 运行记录
GET /api/runs
GET /api/runs/:id

# 知识库
GET    /api/knowledge
POST   /api/knowledge/upload
DELETE /api/knowledge/:id

# 租户管理（admin）
GET  /api/admin/tenants
POST /api/admin/tenants
```

### 7.3 多租户中间件

```
Request → JWT 解析 → 提取 tenant_id, user_id → 注入 Request 对象
       → 所有 DB 查询自动带 tenant_id 过滤
```

---

## 8. 项目目录结构

```
jwworkflow/
├── backend/
│   ├ app/
│   │  ├ main.py                    # FastAPI 入口 + 路由注册
│   │  ├ config.py                  # 配置（数据库/LLM/存储）
│   │  ├ database.py                # SQLAlchemy + pgvector
│   │  ├ api/                       # 路由层
│   │  │  ├ auth.py                 # 登录/注册/JWT
│   │  │  ├ workflows.py            # 工作流 CRUD
│   │  │  ├ runs.py                 # 运行 + SSE 推流
│   │  │  ├ knowledge.py            # 知识库
│   │  │  ├ tenants.py              # 租户管理
│   │  │  └ users.py                # 用户管理
│   │  ├ engine/                    # 工作流引擎（核心）
│   │  │  ├ dag.py                  # DAG 解析 + 拓扑排序
│   │  │  ├ executor.py             # 同步执行引擎
│   │  │  ├ context.py              # 执行上下文
│   │  │  ├ registry.py             # 节点注册表
│   │  │  └ sse.py                  # SSE 事件推送
│   │  ├ nodes/                     # 节点执行器（每类一个文件）
│   │  │  ├ __init__.py             # 注册所有节点
│   │  │  ├ base.py                 # BaseNodeExecutor 接口
│   │  │  ├ llm.py
│   │  │  ├ knowledge.py
│   │  │  ├ agent.py
│   │  │  ├ code_executor.py
│   │  │  ├ if_else.py
│   │  │  ├ iteration.py
│   │  │  ├ http_request.py
│   │  │  ├ template.py
│   │  │  ├ doc_extractor.py
│   │  │  ├ human_input.py
│   │  │  ├ variable_aggregator.py
│   │  │  ├ answer.py
│   │  │  └ output.py
│   │  ├ models/                    # SQLAlchemy ORM 模型
│   │  │  ├ tenant.py
│   │  │  ├ user.py
│   │  │  ├ workflow.py
│   │  │  ├ run.py
│   │  │  ├ document.py
│   │  │  └ embedding.py
│   │  ├ schemas/                   # Pydantic 请求/响应模型
│   │  ├ services/                  # 业务逻辑层
│   │  │  ├ workflow_service.py
│   │  │  ├ knowledge_service.py
│   │  │  ├ rag_service.py          # 文档解析→分块→嵌入→检索
│   │  │  └ llm_service.py          # LLM 调用封装
│   │  └ middleware/                # JWT认证/多租户/限流
│   ├ alembic/                      # 数据库迁移
│   ├ tests/                        # TDD 测试
│   ├ requirements.txt
│   └ Dockerfile
├── frontend/
│   ├ src/
│   ├ package.json
│   └ Dockerfile
├── docker-compose.yml              # PostgreSQL + 后端 + 前端
└── docs/
```

---

## 9. MVP 迭代路线图

### Phase 1: 基础设施（Week 1-2）

- FastAPI 脚手架搭建
- SQLAlchemy 模型 + Alembic 迁移
- JWT 认证注册登录
- 多租户中间件
- Docker Compose 编排
- CI 流水线

**🎯 里程碑**：`docker-compose up` 能启动 + 注册登录

### Phase 2: 工作流引擎核心（Week 2-3）

- DAG 解析 + 拓扑排序
- 节点注册表
- 执行上下文
- 同步执行引擎
- 基础节点（Input/LLM/Template/Output）
- SSE 推送

**🎯 里程碑**：API 触发线性工作流执行成功

### Phase 3: 前端画布（Week 3-4）

- React + React Flow 集成
- 节点调色板（拖拽到画布）
- 自定义节点组件
- 边连接
- 节点配置面板
- 工作流 CRUD UI

**🎯 里程碑**：画布上拖拽出工作流 → 保存 → 加载

### Phase 4: 完整执行闭环（Week 4-5）

- 画布 → 保存 → 触发执行 → SSE 实时状态 → 结果展示
- 控制流节点（If-Else/迭代/人工输入）
- 数据处理节点（代码/HTTP/文档提取）
- 变量聚合器
- 运行历史页面

**🎯 里程碑**：完整工作流拖拽→执行→结果的闭环

### Phase 5: 知识库 + RAG（Week 5-6）

- 文档上传 → 解析（PDF/DOCX/TXT）
- 分块 → Embedding → pgvector 存储
- 混合检索（向量 + 全文搜索）
- 知识库管理 UI
- 知识检索节点

**🎯 里程碑**：上传文档 → 工作流中检索 → LLM 回答

### Phase 6: Agent + 场景接入（Week 6-8）

- Agent 节点（工具调用）
- 已有场景智能体适配
- Chatflow 多轮对话
- 工作流模板
- 运行历史与监控

**🎯 里程碑**：Agent 节点调用已有场景智能体

---

## 10. 非功能性需求

### 10.1 TDD 开发约束

根据 CLAUDE.md 和 LOOP.md：

- 测试先行：先写测试 → 失败 → 实现 → 通过 → 重构
- 小步提交：每个任务 ≤ 30 分钟
- 覆盖率：单元测试 ≥ 80%，核心业务 ≥ 95%
- 自动验证：lint → unit test → integration test → build

### 10.2 性能目标（MVP）

- 单工作流执行：≤ 30s（含 LLM 调用）
- 并发用户：10+ 同时使用
- 工作流吞吐：≥ 5/min per 实例

### 10.3 安全

- JWT 令牌认证（Access + Refresh Token）
- 密码 bcrypt 哈希
- 租户数据隔离（tenant_id 硬过滤）
- API 限流（依赖 FastAPI 中间件）

---

## 11. 与竞品对比定位

| 维度 | Dify | jwworkflow (MVP) |
|------|------|-----------------|
| 目标用户 | 开发者 + 业务 | 业务专家优先 |
| 部署 | 自建 + Cloud | SaaS 多租户优先 |
| 节点数 | 22+ | 15（精准剪裁） |
| 数据层 | PG+Redis+Milvus+S3+Celery | PG only + pgvector |
| 许可证 | 非 OSI（限制托管） | 自有，无限制 |
| 行业场景 | 通用 | 政企招采/纪检/信访等深度场景 |

---

## 12. Design Decisions Log

| 日期 | 决策 | 选项 | 理由 |
|------|------|------|------|
| 2026-07-11 | 架构路线 | A. 全栈自建 | 完全掌控、无许可证顾虑 |
| 2026-07-11 | 目标用户 | A. 业务专家 | 零代码可视化拖拽 |
| 2026-07-11 | 部署模式 | SaaS 多租户 | 快速验证市场 |
| 2026-07-11 | 数据层 | PostgreSQL only + pgvector | 单机可启动，MVP 快速验证 |
| 2026-07-11 | 执行模式 | 同步 + SSE | 避免消息队列复杂度 |
| 2026-07-11 | 节点体系 | 15 种（裁剪自 Dify 22 种） | MVP 聚焦核心编排能力 |
