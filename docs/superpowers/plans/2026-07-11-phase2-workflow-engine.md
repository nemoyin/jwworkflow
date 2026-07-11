# Phase 2: 工作流引擎核心 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 jwworkflow 工作流引擎核心——DAG 解析、节点注册表、执行上下文、同步执行引擎、SSE 推流、基础节点（Input/LLM/Template/Output）及 Workflow CRUD API。

**Architecture:** 引擎位于 `backend/app/engine/`（DAG/执行器/上下文/SSE），节点执行器位于 `backend/app/nodes/`（每类一个文件）。Workflow/Run API 位于 `backend/app/api/`，通过 FastAPI 依赖注入调用引擎。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, pytest, Pydantic, SSE (Server-Sent Events)

## Global Constraints

- 严格 TDD：先写测试 → 失败 → 实现 → 通过 → 重构
- 每个 Task ≤ 30 分钟
- 单元测试覆盖率 ≥ 80%
- Conventional Commits
- 项目根目录：`D:\AI\opc\jwworkflow`
- Git Bash on Windows，路径用 POSIX 风格

---

### Task 1: DAG 定义模型 + 拓扑排序

**Files:**
- Create: `backend/app/engine/dag.py`
- Create: `backend/app/engine/__init__.py`
- Create: `backend/tests/test_dag.py`

**Interfaces:**
- Consumes: 无（纯 Python 数据结构操作）
- Produces: `WorkflowDag(nodes, edges)` — DAG 容器类；`topological_sort(dag) -> list[list[Node]]` — 分层拓扑排序

- [ ] **Step 1: 写 DAG 测试**

```python
# backend/tests/test_dag.py
import pytest
from app.engine.dag import WorkflowDag, topological_sort

class TestWorkflowDag:
    def test_linear_dag(self):
        """验证线性 DAG 拓扑排序"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {}},
                {"id": "n2", "type": "llm", "config": {}},
                {"id": "n3", "type": "output", "config": {}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        )
        levels = topological_sort(dag)
        # n1 -> n2 -> n3
        assert len(levels) == 3
        assert levels[0][0]["id"] == "n1"
        assert levels[1][0]["id"] == "n2"
        assert levels[2][0]["id"] == "n3"

    def test_branching_dag(self):
        """验证分支 DAG：n1 -> n2, n1 -> n3"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {}},
                {"id": "n2", "type": "llm", "config": {}},
                {"id": "n3", "type": "llm", "config": {}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n1", "target": "n3"},
            ]
        )
        levels = topological_sort(dag)
        assert len(levels) == 2  # n1, then n2+n3
        assert levels[0][0]["id"] == "n1"
        assert len(levels[1]) == 2  # n2 and n3 are parallel

    def test_cycle_dag_raises_error(self):
        """验证循环 DAG 抛出异常"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {}},
                {"id": "n2", "type": "llm", "config": {}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n1"},  # cycle
            ]
        )
        with pytest.raises(ValueError, match="cycle"):
            topological_sort(dag)

    def test_get_node(self):
        """验证按 ID 获取节点"""
        dag = WorkflowDag(
            nodes=[{"id": "n1", "type": "input", "config": {}}],
            edges=[]
        )
        node = dag.get_node("n1")
        assert node["id"] == "n1"
        assert dag.get_node("nonexistent") is None

    def test_get_upstream_nodes(self):
        """验证获取上游节点"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input"},
                {"id": "n2", "type": "llm"},
                {"id": "n3", "type": "output"},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        )
        upstream = dag.get_upstream_nodes("n3")
        assert len(upstream) == 2
        assert "n1" in [n["id"] for n in upstream]
        assert "n2" in [n["id"] for n in upstream]
```

- [ ] **Step 2: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_dag.py -v
```
Expected: ImportError — `app.engine.dag` 不存在

- [ ] **Step 3: 实现 DAG 模型**

```python
# backend/app/engine/dag.py
from collections import defaultdict, deque


class WorkflowDag:
    """工作流 DAG 定义容器"""

    def __init__(self, nodes: list[dict], edges: list[dict]):
        self.nodes = nodes
        self.edges = edges
        self._node_map = {n["id"]: n for n in nodes}
        self._build_adjacency()

    def _build_adjacency(self):
        """构建邻接表"""
        self.in_degree = defaultdict(int)
        self.graph = defaultdict(list)
        for node in self.nodes:
            self.in_degree[node["id"]] = 0  # 确保所有节点在 in_degree 中
        for edge in self.edges:
            src, tgt = edge["source"], edge["target"]
            self.graph[src].append(tgt)
            self.in_degree[tgt] += 1

    def get_node(self, node_id: str) -> dict | None:
        """按 ID 获取节点"""
        return self._node_map.get(node_id)

    def get_upstream_nodes(self, node_id: str) -> list[dict]:
        """获取指定节点的所有上游节点"""
        upstream = []
        for edge in self.edges:
            if edge["target"] == node_id:
                upstream.append(self._node_map[edge["source"]])
        return upstream


def topological_sort(dag: WorkflowDag) -> list[list[dict]]:
    """分层拓扑排序，返回按执行顺序排列的节点层列表

    每层内的节点可并行执行，层与层之间顺序执行。
    如检测到循环则抛出 ValueError。
    """
    in_degree = dag.in_degree.copy()
    graph = dag.graph
    node_map = dag._node_map

    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    levels = []

    while queue:
        level_nodes = []
        for _ in range(len(queue)):
            nid = queue.popleft()
            level_nodes.append(node_map[nid])
            for neighbor in graph[nid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        levels.append(level_nodes)

    # 检查是否有未处理的节点（循环）
    if sum(in_degree.values()) > 0:
        raise ValueError("DAG contains a cycle")

    return levels
```

- [ ] **Step 4: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_dag.py -v
```
Expected: 5/5 PASSED

- [ ] **Step 5: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/engine/ backend/tests/test_dag.py
git commit -m "feat: add DAG definition model and topological sort"
```

---

### Task 2: 执行上下文 ExecutionContext

**Files:**
- Create: `backend/app/engine/context.py`
- Create: `backend/tests/test_context.py`

**Interfaces:**
- Consumes: 无
- Produces: `ExecutionContext(inputs)` — 以 node_id 为 key 的变量存储，`set(node_id, output)`, `get(node_id)`, `resolve_variable(expr)` 方法

- [ ] **Step 1: 写 ExecutionContext 测试**

```python
# backend/tests/test_context.py
import pytest
from app.engine.context import ExecutionContext

class TestExecutionContext:
    def test_set_and_get(self):
        """验证设置和获取节点输出"""
        ctx = ExecutionContext({"query": "test"})
        ctx.set("n1", {"result": "hello"})
        assert ctx.get("n1") == {"result": "hello"}

    def test_get_nonexistent_node(self):
        """验证获取不存在的节点抛出 KeyError"""
        ctx = ExecutionContext({})
        with pytest.raises(KeyError):
            ctx.get("nonexistent")

    def test_resolve_simple_variable(self):
        """验证解析 {{ n1.output.field }} 变量"""
        ctx = ExecutionContext({"input_text": "world"})
        ctx.set("n1", {"summary": "hello world"})
        result = ctx.resolve_variable("{{ n1.summary }}")
        assert result == "hello world"

    def test_resolve_input_variable(self):
        """验证解析 {{ input.field }} 变量"""
        ctx = ExecutionContext({"query": "test_query"})
        result = ctx.resolve_variable("{{ input.query }}")
        assert result == "test_query"

    def test_resolve_nested_field(self):
        """验证解析嵌套字段"""
        ctx = ExecutionContext({})
        ctx.set("n1", {"data": {"score": 0.95, "label": "合规"}})
        result = ctx.resolve_variable("{{ n1.data.score }}")
        assert result == 0.95

    def test_get_inputs(self):
        """验证获取原始输入"""
        ctx = ExecutionContext({"query": "test"})
        assert ctx.inputs == {"query": "test"}
```

- [ ] **Step 2: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_context.py -v
```
Expected: ImportError

- [ ] **Step 3: 实现 ExecutionContext**

```python
# backend/app/engine/context.py
import re
from functools import reduce


class ExecutionContext:
    """工作流执行上下文，管理节点间变量传递"""

    VARIABLE_PATTERN = re.compile(r"\{\{\s*([^}]+)\s*\}\}")

    def __init__(self, inputs: dict):
        self._inputs = inputs
        self._outputs: dict[str, dict] = {}

    @property
    def inputs(self) -> dict:
        return self._inputs

    def set(self, node_id: str, output: dict):
        """存储节点输出"""
        self._outputs[node_id] = output

    def get(self, node_id: str) -> dict:
        """获取节点输出"""
        if node_id not in self._outputs:
            raise KeyError(f"Node {node_id} has no output yet")
        return self._outputs[node_id]

    def resolve_variable(self, expression: str) -> any:
        """解析变量引用表达式

        支持格式:
        - {{ n1.field.subfield }}
        - {{ input.var_name }}
        - 纯文本 (无变量, 原样返回)
        """
        match = self.VARIABLE_PATTERN.search(expression)
        if not match:
            return expression

        path = match.group(1).strip().split(".")
        source = path[0]

        if source == "input":
            value = self._inputs
        else:
            if source not in self._outputs:
                raise KeyError(f"Cannot resolve '{expression}': node '{source}' has no output")
            value = self._outputs[source]

        # 按路径逐层访问
        for key in path[1:]:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                raise KeyError(f"Cannot resolve '{expression}': '{key}' not found")
            if value is None:
                raise KeyError(f"Cannot resolve '{expression}': '{key}' is None")

        return value
```

- [ ] **Step 4: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_context.py -v
```
Expected: 5/5 PASSED

- [ ] **Step 5: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/engine/context.py backend/tests/test_context.py
git commit -m "feat: add ExecutionContext for variable passing"
```

---

### Task 3: 节点注册表 + 基础节点 (Input/LLM/Template/Output)

**Files:**
- Create: `backend/app/nodes/base.py`
- Create: `backend/app/nodes/registry.py`
- Create: `backend/app/nodes/input_node.py`
- Create: `backend/app/nodes/llm_node.py`
- Create: `backend/app/nodes/template_node.py`
- Create: `backend/app/nodes/output_node.py`
- Update: `backend/app/nodes/__init__.py`
- Create: `backend/tests/test_registry.py`
- Create: `backend/tests/test_node_input.py`
- Create: `backend/tests/test_node_template.py`
- Create: `backend/tests/test_node_output.py`

**Interfaces:**
- Consumes: `app.engine.context.ExecutionContext`
- Produces: `BaseNodeExecutor` — 抽象基类；`NODE_REGISTRY` — 节点类型映射；基础节点实现

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_registry.py
import pytest
from app.nodes.base import BaseNodeExecutor
from app.nodes.registry import NODE_REGISTRY, register_node, get_node

class TestNodeRegistry:
    def test_register_and_get(self):
        """验证注册和获取节点执行器"""
        registry = {}
        class TestNode(BaseNodeExecutor):
            def execute(self, ctx, config):
                return {"result": "test"}
        register_node(registry, "test", TestNode)
        cls = get_node(registry, "test")
        assert cls is TestNode

    def test_get_nonexistent(self):
        """验证获取不存在的节点返回 None"""
        assert get_node({}, "nonexistent") is None
```

```python
# backend/tests/test_node_input.py
import pytest
from app.engine.context import ExecutionContext
from app.nodes.input_node import InputNodeExecutor

class TestInputNode:
    def test_input_returns_fields(self):
        """验证输入节点返回字段"""
        executor = InputNodeExecutor()
        ctx = ExecutionContext({"query": "hello", "file": None})
        config = {"fields": [{"name": "query", "type": "text"}]}
        result = executor.execute(ctx, config)
        assert result == {"query": "hello"}

    def test_input_empty_config(self):
        """验证空配置返回空字典"""
        executor = InputNodeExecutor()
        ctx = ExecutionContext({"query": "hello"})
        result = executor.execute(ctx, {"fields": []})
        assert result == {}
```

```python
# backend/tests/test_node_template.py
import pytest
from app.engine.context import ExecutionContext
from app.nodes.template_node import TemplateNodeExecutor

class TestTemplateNode:
    def test_template_renders_variables(self):
        """验证模板渲染变量"""
        executor = TemplateNodeExecutor()
        ctx = ExecutionContext({"query": "test"})
        ctx.set("n1", {"summary": "hello world"})
        config = {"template": "Result: {{ n1.summary }}, Query: {{ input.query }}"}
        result = executor.execute(ctx, config)
        assert result == {"output": "Result: hello world, Query: test"}

    def test_template_no_variables(self):
        """验证无变量模板原样输出"""
        executor = TemplateNodeExecutor()
        ctx = ExecutionContext({})
        config = {"template": "Plain text"}
        result = executor.execute(ctx, config)
        assert result == {"output": "Plain text"}
```

```python
# backend/tests/test_node_output.py
import pytest
from app.engine.context import ExecutionContext
from app.nodes.output_node import OutputNodeExecutor

class TestOutputNode:
    def test_output_returns_selected_variables(self):
        """验证输出节点返回选中的变量"""
        executor = OutputNodeExecutor()
        ctx = ExecutionContext({"query": "test"})
        ctx.set("n1", {"result": "hello", "score": 0.95})
        config = {"variables": [{"name": "result", "source": "n1.result"}]}
        result = executor.execute(ctx, config)
        assert result == {"result": "hello"}
```

- [ ] **Step 2: 实现基础节点**

```python
# backend/app/nodes/base.py
from abc import ABC, abstractmethod
from app.engine.context import ExecutionContext


class BaseNodeExecutor(ABC):
    """所有节点执行器的抽象基类"""

    @abstractmethod
    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        """执行节点逻辑

        Args:
            ctx: 执行上下文
            config: 节点配置

        Returns:
            节点输出字典
        """
        pass
```

```python
# backend/app/nodes/registry.py
from app.nodes.base import BaseNodeExecutor


NODE_REGISTRY: dict[str, type[BaseNodeExecutor]] = {}


def register_node(
    registry: dict[str, type[BaseNodeExecutor]],
    node_type: str,
    executor_cls: type[BaseNodeExecutor],
):
    """注册节点执行器到指定注册表"""
    registry[node_type] = executor_cls


def get_node(
    registry: dict[str, type[BaseNodeExecutor]],
    node_type: str,
) -> type[BaseNodeExecutor] | None:
    """从注册表获取节点执行器类"""
    return registry.get(node_type)
```

```python
# backend/app/nodes/input_node.py
from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class InputNodeExecutor(BaseNodeExecutor):
    """输入节点：从工作流输入中提取字段"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        fields = config.get("fields", [])
        result = {}
        for field in fields:
            name = field["name"]
            if name in ctx.inputs:
                result[name] = ctx.inputs[name]
        return result
```

```python
# backend/app/nodes/llm_node.py
from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class LLMNodeExecutor(BaseNodeExecutor):
    """LLM 节点：调用大语言模型推理

    MVP 阶段为桩实现（stub），返回模拟结果。
    Phase 4 接入真实 LLM API。
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        # Stub: 返回配置中的 system_prompt 和模拟输出
        return {
            "output": f"[LLM Stub] 已收到提示词，模型: {config.get('model', 'default')}",
            "model": config.get("model", "default"),
        }
```

```python
# backend/app/nodes/template_node.py
from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class TemplateNodeExecutor(BaseNodeExecutor):
    """模板节点：使用 Jinja2 风格渲染变量"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        template = config.get("template", "")
        rendered = ctx.resolve_variable(template)
        return {"output": rendered}
```

```python
# backend/app/nodes/output_node.py
from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class OutputNodeExecutor(BaseNodeExecutor):
    """输出节点：从执行上下文中提取指定变量返回"""

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        variables = config.get("variables", [])
        result = {}
        for var in variables:
            name = var["name"]
            source = var.get("source", "")
            try:
                resolved = ctx.resolve_variable(f"{{{{ {source} }}}}")
                result[name] = resolved
            except KeyError:
                result[name] = None
        return result
```

- [ ] **Step 3: 注册所有节点**

```python
# backend/app/nodes/__init__.py
from app.nodes.base import BaseNodeExecutor
from app.nodes.registry import NODE_REGISTRY, register_node, get_node
from app.nodes.input_node import InputNodeExecutor
from app.nodes.llm_node import LLMNodeExecutor
from app.nodes.template_node import TemplateNodeExecutor
from app.nodes.output_node import OutputNodeExecutor

# 注册所有内置节点
register_node(NODE_REGISTRY, "input", InputNodeExecutor)
register_node(NODE_REGISTRY, "llm", LLMNodeExecutor)
register_node(NODE_REGISTRY, "template", TemplateNodeExecutor)
register_node(NODE_REGISTRY, "output", OutputNodeExecutor)

__all__ = [
    "BaseNodeExecutor", "NODE_REGISTRY", "register_node", "get_node",
    "InputNodeExecutor", "LLMNodeExecutor",
    "TemplateNodeExecutor", "OutputNodeExecutor",
]
```

- [ ] **Step 4: 运行测试**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_registry.py tests/test_node_input.py tests/test_node_template.py tests/test_node_output.py -v
```
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/nodes/backend/tests/test_registry.py backend/tests/test_node_input.py backend/tests/test_node_template.py backend/tests/test_node_output.py
git commit -m "feat: add node registry and base node types (input/llm/template/output)"
```

---

### Task 4: 同步执行引擎 (Workflow Runner)

**Files:**
- Create: `backend/app/engine/executor.py`
- Create: `backend/app/engine/sse.py`
- Create: `backend/tests/test_executor.py`

**Interfaces:**
- Consumes: `WorkflowDag`, `ExecutionContext`, `NODE_REGISTRY`, `topological_sort`
- Produces: `WorkflowExecutor(dag, node_registry)` — 同步执行引擎，`execute(inputs) -> dict`；SSE 事件缓存

- [ ] **Step 1: 写执行引擎测试**

```python
# backend/tests/test_executor.py
import pytest
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY


class TestWorkflowExecutor:
    def test_linear_execution(self):
        """验证线性工作流完整执行"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "query", "type": "text"}]}},
                {"id": "n2", "type": "template", "config": {"template": "Hello {{ input.query }}"}},
                {"id": "n3", "type": "output", "config": {"variables": [{"name": "greeting", "source": "n2.output"}]}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        result = executor.execute({"query": "World"})
        assert result == {"greeting": "Hello World"}

    def test_execution_returns_all_node_outputs(self):
        """验证执行返回所有节点输出"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "x", "type": "text"}]}},
                {"id": "n2", "type": "output", "config": {"variables": [{"name": "val", "source": "n1.x"}]}},
            ],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        result = executor.execute({"x": "42"})
        assert result == {"val": "42"}

    def test_unknown_node_type_raises_error(self):
        """验证未知节点类型抛出异常"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "nonexistent", "config": {}},
                {"id": "n2", "type": "output", "config": {"variables": []}},
            ],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        with pytest.raises(ValueError, match="Unknown node type"):
            executor.execute({})

    def test_events_recorded_during_execution(self):
        """验证执行过程中记录事件"""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {"fields": []}},
                {"id": "n2", "type": "output", "config": {"variables": []}},
            ],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}]
        )
        executor = WorkflowExecutor(dag, NODE_REGISTRY)
        executor.execute({})
        events = executor.get_events()
        assert len(events) >= 4  # workflow_start, node_start x2, node_done x2, workflow_done
        assert events[0]["type"] == "workflow_start"
        assert events[-1]["type"] == "workflow_done"
```

- [ ] **Step 2: 实现 SSE 事件服务**

```python
# backend/app/engine/sse.py
import json
from datetime import datetime, timezone


class SSEEvent:
    """SSE 事件数据模型"""

    def __init__(self, event_type: str, data: dict):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
        }
```

- [ ] **Step 3: 实现执行引擎**

```python
# backend/app/engine/executor.py
from app.engine.dag import WorkflowDag, topological_sort
from app.engine.context import ExecutionContext
from app.engine.sse import SSEEvent
from app.nodes.base import BaseNodeExecutor


class WorkflowExecutor:
    """同步工作流执行引擎"""

    def __init__(self, dag: WorkflowDag, node_registry: dict[str, type[BaseNodeExecutor]]):
        self.dag = dag
        self.node_registry = node_registry
        self._events: list[SSEEvent] = []

    def execute(self, inputs: dict) -> dict:
        """同步执行工作流

        Args:
            inputs: 工作流输入参数字典

        Returns:
            输出节点返回的结果字典

        Raises:
            ValueError: 遇到未知节点类型
        """
        ctx = ExecutionContext(inputs)
        self._add_event("workflow_start", {"inputs": inputs})

        levels = topological_sort(self.dag)
        output_result = {}

        for level in levels:
            for node in levels:
                # 查找输出节点（最后处理）
                pass

        for level in levels:
            for node in level:
                node_type = node["type"]
                executor_cls = self.node_registry.get(node_type)
                if executor_cls is None:
                    raise ValueError(f"Unknown node type: {node_type}")

                executor = executor_cls()
                config = node.get("config", {})

                self._add_event("node_start", {"node_id": node["id"], "node_type": node_type})

                try:
                    result = executor.execute(ctx, config)
                    ctx.set(node["id"], result)
                    self._add_event("node_done", {"node_id": node["id"], "output": result})
                except Exception as e:
                    self._add_event("node_error", {"node_id": node["id"], "error": str(e)})
                    # 默认错误策略：终止执行
                    raise

                # 如果是输出节点，记录最终结果
                if node_type == "output":
                    output_result = result

        self._add_event("workflow_done", {"output": output_result})
        return output_result

    def get_events(self) -> list[dict]:
        """获取执行事件列表"""
        return [e.to_dict() for e in self._events]

    def _add_event(self, event_type: str, data: dict):
        self._events.append(SSEEvent(event_type, data))
```

- [ ] **Step 4: 运行测试**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_executor.py -v
```
Expected: 4/4 PASSED

- [ ] **Step 5: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/engine/executor.py backend/app/engine/sse.py backend/tests/test_executor.py
git commit -m "feat: add synchronous workflow execution engine with SSE events"
```

---

### Task 5: Workflow CRUD + Run API

**Files:**
- Create: `backend/app/schemas/workflow.py`
- Create: `backend/app/api/workflows.py`
- Create: `backend/tests/test_api_workflows.py`
- Modify: `backend/app/main.py` (注册 workflow 路由)

**Interfaces:**
- Consumes: `app.middleware.auth_middleware.get_current_user`, `WorkflowExecutor`, `WorkflowDag`, `NODE_REGISTRY`
- Produces: `POST /api/workflows` — 创建；`GET /api/workflows` — 列表；`GET /api/workflows/:id` — 详情；`PUT /api/workflows/:id` — 更新；`DELETE /api/workflows/:id` — 删除；`POST /api/workflows/:id/run` — 执行；`GET /api/runs/:id` — 运行详情

- [ ] **Step 1: 写 API 测试**

```python
# backend/tests/test_api_workflows.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestWorkflowAPI:
    """工作流 CRUD + 运行 API 测试"""

    @pytest.fixture(scope="class")
    def token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "工作流测试",
            "email": "wf_test@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def sample_workflow(self):
        return {
            "name": "测试工作流",
            "description": "一个简单的测试工作流",
            "type": "workflow",
            "dag_definition": {
                "nodes": [
                    {"id": "n1", "type": "input", "config": {"fields": [{"name": "query", "type": "text"}]}},
                    {"id": "n2", "type": "template", "config": {"template": "Hello {{ input.query }}"}},
                    {"id": "n3", "type": "output", "config": {"variables": [{"name": "greeting", "source": "n2.output"}]}},
                ],
                "edges": [
                    {"id": "e1", "source": "n1", "target": "n2"},
                    {"id": "e2", "source": "n2", "target": "n3"},
                ]
            }
        }

    def test_create_workflow(self, headers, sample_workflow):
        """验证创建工作流"""
        resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "测试工作流"
        assert "id" in data

    def test_list_workflows(self, headers):
        """验证获取工作流列表"""
        resp = client.get("/api/workflows", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_workflow(self, headers, sample_workflow):
        """验证获取工作流详情"""
        create_resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        wf_id = create_resp.json()["id"]

        resp = client.get(f"/api/workflows/{wf_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "测试工作流"

    def test_run_workflow(self, headers, sample_workflow):
        """验证执行工作流返回结果"""
        create_resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        wf_id = create_resp.json()["id"]

        resp = client.post(f"/api/workflows/{wf_id}/run",
                           json={"query": "World"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert data["result"] == {"greeting": "Hello World"}

    def test_delete_workflow(self, headers, sample_workflow):
        """验证删除工作流"""
        create_resp = client.post("/api/workflows", json=sample_workflow, headers=headers)
        wf_id = create_resp.json()["id"]

        resp = client.delete(f"/api/workflows/{wf_id}", headers=headers)
        assert resp.status_code == 204
```

- [ ] **Step 2: 创建 Workflow ORM 模型**

```python
# backend/app/models/workflow.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, default="")
    type: Mapped[str] = Column(String(32), default="workflow")  # workflow | chatflow
    dag_definition: Mapped[dict] = Column(JSON, nullable=False)
    version: Mapped[int] = Column(Integer, default=1)
    status: Mapped[str] = Column(String(32), default="draft")  # draft | published
    created_by: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

```python
# backend/app/models/run.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    triggered_by: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = Column(String(32), default="running")  # running | success | failed
    input: Mapped[dict] = Column(JSON, default=dict)
    output: Mapped[dict] = Column(JSON, default=dict)
    error: Mapped[str] = Column(Text, nullable=True)
    duration_ms: Mapped[int] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 3: 创建 Schema**

```python
# backend/app/schemas/workflow.py
from pydantic import BaseModel
from typing import Optional


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    type: str = "workflow"
    dag_definition: dict


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dag_definition: Optional[dict] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    dag_definition: dict
    status: str
    version: int
    created_at: str


class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    duration_ms: int | None = None
    created_at: str
```

- [ ] **Step 4: 实现 Workflow API**

```python
# backend/app/api/workflows.py
import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.run import Run
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse, RunResponse
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.nodes import NODE_REGISTRY

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("", status_code=201, response_model=WorkflowResponse)
async def create_workflow(
    body: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建工作流"""
    wf = Workflow(
        tenant_id=current_user.tenant_id,
        name=body.name,
        description=body.description,
        type=body.type,
        dag_definition=body.dag_definition,
        created_by=current_user.id,
    )
    db.add(wf)
    await db.flush()
    return WorkflowResponse(
        id=str(wf.id), name=wf.name, description=wf.description or "",
        type=wf.type, dag_definition=wf.dag_definition,
        status=wf.status, version=wf.version,
        created_at=wf.created_at.isoformat(),
    )


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流列表"""
    result = await db.execute(
        select(Workflow).where(Workflow.tenant_id == current_user.tenant_id)
    )
    workflows = result.scalars().all()
    return [
        WorkflowResponse(
            id=str(w.id), name=w.name, description=w.description or "",
            type=w.type, dag_definition=w.dag_definition,
            status=w.status, version=w.version,
            created_at=w.created_at.isoformat(),
        )
        for w in workflows
    ]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流详情"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return WorkflowResponse(
        id=str(wf.id), name=wf.name, description=wf.description or "",
        type=wf.type, dag_definition=wf.dag_definition,
        status=wf.status, version=wf.version,
        created_at=wf.created_at.isoformat(),
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新工作流"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if body.name is not None:
        wf.name = body.name
    if body.description is not None:
        wf.description = body.description
    if body.dag_definition is not None:
        wf.dag_definition = body.dag_definition
    wf.version += 1
    await db.flush()
    return WorkflowResponse(
        id=str(wf.id), name=wf.name, description=wf.description or "",
        type=wf.type, dag_definition=wf.dag_definition,
        status=wf.status, version=wf.version,
        created_at=wf.created_at.isoformat(),
    )


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除工作流"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    await db.delete(wf)
    await db.flush()


@router.post("/{workflow_id}/run", response_model=RunResponse)
async def run_workflow(
    workflow_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行工作流"""
    # 加载工作流定义
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 构建 DAG 并执行
    dag = WorkflowDag(
        nodes=wf.dag_definition.get("nodes", []),
        edges=wf.dag_definition.get("edges", []),
    )
    executor = WorkflowExecutor(dag, NODE_REGISTRY)

    start_time = time.time()
    try:
        output = executor.execute(body)
        duration = int((time.time() - start_time) * 1000)
        status_val = "success"
        error_text = None
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        status_val = "failed"
        output = {}
        error_text = str(e)

    # 保存运行记录
    run = Run(
        workflow_id=wf.id,
        tenant_id=current_user.tenant_id,
        triggered_by=current_user.id,
        status=status_val,
        input=body,
        output=output,
        error=error_text,
        duration_ms=duration,
    )
    db.add(run)
    await db.flush()

    if status_val == "failed":
        raise HTTPException(status_code=500, detail=error_text)

    return RunResponse(
        id=str(run.id),
        workflow_id=str(run.workflow_id),
        status=run.status,
        result=run.output,
        duration_ms=run.duration_ms,
        created_at=run.created_at.isoformat(),
    )
```

- [ ] **Step 5: 注册路由 + 迁移**

```python
# 在 backend/app/main.py 中添加
from app.api import workflows as workflows_router
app.include_router(workflows_router.router)
```

```bash
cd /d/AI/opc/jwworkflow/backend
alembic revision --autogenerate -m "add workflow and run models"
alembic upgrade head
```

- [ ] **Step 6: 运行全量测试**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/ -v
```
Expected: All PASSED

- [ ] **Step 7: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add -A
git commit -m "feat: add workflow CRUD API and run endpoint"
```

---

## Phase 2 完整测试清单

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/ -v --cov=app --cov-report=term-missing
```

**预期测试数：** 28+（5 DAG + 5 Context + 4 Registry + 2 Input + 2 Template + 2 Output + 4 Executor + 5 Workflow API + 21 Phase 1 existing）
**覆盖率目标：** ≥ 80%
