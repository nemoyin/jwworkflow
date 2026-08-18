# jwworkflow — 通用 LLM Agent 工作流编排平台

> 面向非技术用户的零代码 AI 工作流编排平台，通过可视化拖拽搭建 LLM Agent 工作流，赋能政企场景智能化转型。

![GitHub](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)

---

## 📋 目录

- [产品定位](#-产品定位)
- [核心能力](#-核心能力)
- [架构总览](#-架构总览)
- [快速启动](#-快速启动)
- [开发指南](#-开发指南)
- [API 文档](#-api-文档)
- [场景模板](#-预置场景模板)
- [测试](#-测试)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)

---

## 🎯 产品定位

jwworkflow 是一个**面向业务专家（非技术用户）的通用 LLM Agent 工作流编排平台**，通过可视化拖拽搭建 AI 工作流，覆盖以下场景：

| 场景 | 说明 |
|------|------|
| 📄 招标文件合规审查 | 自动检索法规条款，LLM 判定并生成审查报告 |
| 🔍 围串标分析 | 分析投标文件中的围标、串标嫌疑特征 |
| 💬 纪检模拟谈话 | AI 扮演谈话人，进行纪律审查谈话模拟训练 |
| 📊 AI 问数 | 自然语言提问，AI 自动理解并返回分析结果 |
| 📞 12345 投诉舆情分析 | 智能分类、 sentiment 分析、自动转办建议 |
| ✉️ 智慧信访 | 信访内容智能分派、重复件识别、办理建议 |
| ⚖️ 定性量纪辅助 | 基于规则+案例的纪律处分建议 |
| 📑 三书比对 | 多版本文书自动比对差异 |
| 🛒 国企招采比价 | 采购价格智能比对分析 |
| 🎓 小升初择优面试 | 小升初面试择优选拔演练（AI 面试老师按模式提问，支持数字人访谈） |

---

## 🚀 核心能力

### 可视化工作流编排

通过拖拽方式构建 AI 工作流，支持 14 种节点类型：

| 类别 | 节点 | 说明 |
|------|------|------|
| **入口** 🟢 | 用户输入、Webhook | 定义输入字段和触发方式 |
| **AI** 🔵 | LLM、知识检索(RAG)、Agent | 大模型推理、知识库检索、自主工具调用 |
| **逻辑** 🟣 | 条件分支(If-Else)、迭代、人工输入 | 流程控制与人工审核 |
| **数据处理** 🟠 | 代码执行、模板渲染、HTTP 请求、文档提取、变量聚合 | 转换与集成 |
| **输出** 🟢 | 输出（文本/文件/JSON） | 结果导出 |

### 执行引擎

- **DAG 驱动** — 有向无环图拓扑排序，支持并行节点执行
- **同步执行 + SSE 推流** — 实时推送节点执行状态到前端
- **变量传递** — `{{ node_id.field }}` 语法引用上游节点输出

### 多模型管理

- 支持多个 LLM 供应商（DeepSeek / OpenAI / Ollama / Azure / Anthropic / Google）
- 模型注册表统一管理，每个模型带能力标签
- 节点执行时自动查找模型所属供应商
- 模型调试功能实时测试连通性

### 多租户 + RBAC

- 租户间数据严格隔离（`tenant_id` 行级过滤）
- 用户角色：`admin` / `member`
- 用户管理：邀请、角色变更、启用/禁用

### RAG 知识库

- 支持 PDF / DOCX / TXT 文档上传
- 自动解析→分块→Embedding→pgvector 存储
- 混合检索（向量相似度 + 全文搜索）

### AI 数字人访谈

- 全屏沉浸式数字人访谈门户（STT → LLM → TTS 实时语音循环）
- 与 Chatflow 对话流深度结合：`system_prompt` 内以 `{{ input.xxx }}` 渲染场景、对象、模式等上下文
- 多轮口语交互，适用于小升初面试、模拟谈话、产品讲解等演练场景

---

## 🏗 架构总览

```
Frontend (React + React Flow + Ant Design)
    │ REST / SSE
Backend (FastAPI + SQLAlchemy)
    ├─ engine/       DAG 解析 | ExecutionContext | WorkflowExecutor | SSE
    ├─ nodes/        14 种节点执行器 (LLM/Code/HTTP/RAG/Agent...)
    ├─ agents/       场景智能体框架 (合规/围串标/谈话)
    ├─ services/     RAG 管道 | LLM 调用 | Embedding
    └─ api/          Workflow CRUD | Auth | Knowledge | Chat | Templates
DB (SQLite 内置 / PostgreSQL + pgvector 可选)
```

### 数据层

```
Docker 打包形态（默认，无外部依赖）
  └─ SQLite（sqlite+aiosqlite，jwworkflow.db）——模板/工作流/对话记录全部固化在后端镜像内
  └─ 本地文件系统（替代 MinIO/S3）
      └─ /data/uploads/   上传文档
      └─ /data/knowledge/ 知识库文件

可选形态（通过 DATABASE_URL 切换）
  └─ PostgreSQL 16 + pgvector 扩展 = 内置向量库（无需额外部署 Milvus）

❌ 去除：Celery / RabbitMQ / Redis / MinIO / Milvus
   └─ 工作流改为同步执行（长任务用 SSE 推送进度）
```

---

## ⚡ 快速启动

### 方式一：Docker Compose（推荐）

后端与前端各为独立镜像（`jwworkflow-backend` / `jwworkflow-frontend`），由 `docker-compose.yml` 编排。**模板、实例化工作流、对话记录等持久化数据以 SQLite 快照固化在后端镜像内**（`/app/jwworkflow.db`），开箱即用、无需外部数据库。

```bash
git clone <your-repo-url>
cd jwworkflow

# 一键构建并启动
docker compose build
docker compose up -d

# 访问前端 http://localhost:8088 （后端 API 端口 18000，健康检查 /health）
```

> **国内网络构建注意**：backend 构建使用阿里云 PyPI 镜像（`mirrors.aliyun.com`），frontend 使用 npmmirror registry，避免官方源超时/SSL 阻断。

#### 镜像打包与离线分发

数据已固化在镜像内，可用 `docker save` 导出为单个 tar 包，离线环境 `docker load` 后直接运行：

```bash
# 本机导出（含前后端两个镜像）
docker save -o jwworkflow.tar jwworkflow-backend:latest jwworkflow-frontend:latest

# 目标机加载并启动
docker load -i jwworkflow.tar
docker compose up -d     # 访问 http://<host>:8088
```

### 方式二：本地开发

**后端：**

```bash
cd backend
pip install -r requirements.txt
JWT_SECRET=my-secret LLM_API_KEY=sk-xxx uvicorn app.main:app --reload --port 8080
```

**前端：**

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

### 默认账号

| 用户名 | 密码 |
|--------|------|
| `admin@demo.com` | `demo123` |

---

## 🧪 测试

### 后端测试（275 个）

```bash
cd backend
JWT_SECRET=test-secret LLM_API_KEY="" pytest tests/ -v
```

### 前端 E2E 测试（8 个）

```bash
cd frontend
npx playwright test --reporter=list
```

---

## 📚 API 文档

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册（创建租户+管理员） |
| POST | `/api/auth/login` | 登录获取 JWT |
| GET | `/api/auth/me` | 当前用户信息 |

### 工作流

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/workflows` | 创建 |
| GET | `/api/workflows` | 列表 |
| GET | `/api/workflows/:id` | 详情 |
| PUT | `/api/workflows/:id` | 更新 |
| DELETE | `/api/workflows/:id` | 删除 |
| POST | `/api/workflows/:id/run` | 执行 |

### 模型管理

| 方法 | 路径 | 说明 |
|------|------|------|
| CRUD | `/api/admin/providers` | LLM 供应商管理 |
| CRUD | `/api/admin/models` | 模型注册表 |
| GET | `/api/admin/models/available` | 可用于下拉选择的模型 |
| POST | `/api/admin/models/:id/test` | 调试/测试模型连通性 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/upload` | 上传文档 |
| GET | `/api/knowledge` | 文档列表 |
| DELETE | `/api/knowledge/:id` | 删除文档 |

### 管理后台

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/tenants` | 租户列表（admin） |
| GET | `/api/admin/users` | 用户列表 |
| POST | `/api/admin/users` | 邀请用户 |
| PUT/DELETE | `/api/admin/users/:id` | 更新/删除用户 |

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/conversations` | 创建对话 |
| POST | `/api/conversations/:id/messages` | 发送消息 |
| GET | `/api/conversations/:id/messages` | 历史消息 |

### 模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/templates` | 模板列表 |
| POST | `/api/templates/:id/instantiate` | 从模板创建工作流 |

---

## 📦 预置场景模板

| 模板 | 节点构成 | 适用场景 |
|------|---------|---------|
| **招标合规审查** | `input → knowledge_retrieval → llm → output` | 招标文件合规性自动审查 |
| **围串标分析** | `input → code → llm → output` | 投标文件围标串标风险分析 |
| **纪检模拟谈话** | `input → agent → output` | 纪检监察谈话模拟演练 |
| **AI 问数** | `input → llm → output` | 自然语言数据查询与分析 |
| **小升初择优面试** | `input → agent(chat) → output` | 小升初面试择优演练；输入学校/学生信息与面试模式（自适应/压力/学术/表达等 8 种），AI 面试老师多轮提问，支持数字人访谈 |

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 18 + TypeScript + Vite |
| **画布** | React Flow (v11) |
| **UI 组件** | Ant Design 5 |
| **状态管理** | Zustand |
| **后端** | Python 3.11+ / FastAPI |
| **ORM** | SQLAlchemy 2.0 + Alembic |
| **数据库** | SQLite（Docker 打包内置）/ PostgreSQL 16 + pgvector（可选） |
| **LLM 集成** | OpenAI 兼容 SDK（支持 DeepSeek / OpenAI / Ollama 等） |
| **测试** | pytest (后端) / Playwright (前端 E2E) |
| **容器化** | Docker Compose 双镜像编排 + docker save 离线分发 |

---

## 📁 项目结构

```
jwworkflow/
├── backend/
│   ├ app/
│   │  ├ api/            # FastAPI 路由
│   │  ├ engine/         # 工作流引擎（DAG/执行器/SSE）
│   │  ├ nodes/          # 节点执行器（14 种）
│   │  ├ agents/         # 场景智能体
│   │  ├ models/         # SQLAlchemy ORM 模型
│   │  ├ schemas/        # Pydantic 请求/响应模型
│   │  ├ services/       # 业务逻辑（LLM/RAG）
│   │  └ middleware/     # JWT 认证 / 多租户 / RBAC
│   ├ alembic/           # 数据库迁移
│   ├ tests/             # 275 个测试
│   └ requirements.txt
├── frontend/
│   ├ src/
│   │  ├ pages/          # 页面组件
│   │  ├ components/     # UI 组件（画布/节点/面板）
│   │  ├ stores/         # Zustand 状态管理
│   │  ├ hooks/          # 自定义 Hooks（SSE 等）
│   │  └ services/       # API 客户端
│   ├ e2e/               # Playwright E2E 测试
│   └ package.json
├── docker-compose.yml   # 前后端双镜像编排（后端内置 SQLite 数据快照）
└── docs/                # 设计文档与计划
```

---

## 📝 License

MIT

---

## 🏗 开发路线图

| Phase | 内容 | 状态 |
|-------|------|------|
| **Phase 1** | 基础设施（FastAPI/JWT/多租户/Docker） | ✅ 完成 |
| **Phase 2** | 工作流引擎（DAG/节点/执行器/SSE） | ✅ 完成 |
| **Phase 3** | 前端画布（React Flow/节点 UI/SSE 监控） | ✅ 完成 |
| **Phase 4** | 完整闭环（控制流/数据处理/运行历史） | ✅ 完成 |
| **Phase 5** | 知识库 + RAG（文档管理/向量检索） | ✅ 完成 |
| **Phase 6** | Agent + Chatflow + 场景模板 | ✅ 完成 |
| **Phase 7** | 多模型管理 + RBAC + 租户管理 | ✅ 完成 |
| **Phase 8** | 小升初择优面试模板 + 数字人访谈 | ✅ 完成 |
| **Phase 9** | Docker 双镜像打包（SQLite 数据固化 + docker save 分发）、登录态持久化 | ✅ 完成 |
| **后续** | 真实 LLM 接入、性能优化、更多场景智能体 | 📋 规划中 |
