# Phase 8: 剩余功能实现计划

### Task 1: 规则引擎节点
**后端:** `backend/app/nodes/rule_engine.py` + 注册
**测试:** `backend/tests/test_node_rule_engine.py`
**前端:** 更新 NodePalette + NodeConfigPanel

### Task 2: Webhook 节点
**后端:** `backend/app/nodes/webhook_node.py` + webhook 触发 API
**模型:** `backend/app/models/webhook.py` - webhook 配置
**测试:** `backend/tests/test_node_webhook.py`

### Task 3: Chatflow Answer 节点
**后端:** `backend/app/nodes/answer_node.py` - 流式输出
**前端:** NodePalette + AnswerNode 组件

### Task 4: 工作流 Debug 模式
**后端:** 引擎增加 step-by-step 执行模式，返回中间状态
**API:** `POST /api/workflows/:id/debug` - 单步执行
**前端:** DebugOverlay 组件

### Task 5: 外部集成 (Embed + Preview + API)
**后端:** 
- `GET /api/workflows/:id/preview` - 获取运行所需输入 schema
- `POST /api/workflows/:id/execute` - 外部调用（无认证或 API Key 认证）
**前端:**
- 预览页面 `/preview/:id`
- iframe 嵌入代码生成
- 独立对话框组件
