import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.template import WorkflowTemplate
from app.schemas.template import (
    TemplateResponse,
    TemplateInstantiateRequest,
    TemplateInstantiateResponse,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _ensure_node_positions(dag: dict) -> dict:
    """为没有 position 的节点自动分配布局位置"""
    nodes = dag.get("nodes", [])
    updated = False
    for i, node in enumerate(nodes):
        if "position" not in node:
            nodes[i] = {**node, "position": {"x": 250 * (i % 3), "y": 120 * (i // 3 + 1)}}
            updated = True
    if updated:
        dag["nodes"] = nodes
    return dag

# ---------------------------------------------------------------------------
# Pre-built template definitions
# ---------------------------------------------------------------------------
BUILTIN_TEMPLATES: list[dict] = [
    {
        "name": "招标合规审查",
        "description": "自动检索招标文件相关法规和合规条款，由大语言模型判定并生成合规审查报告。适用于招标文件的合规性审查场景。",
        "category": "compliance",
        "icon": "FileTextOutlined",
        "sort_order": 1,
        "is_builtin": True,
        "dag_definition": {
            "nodes": [
                {
                    "id": "n1",
                    "type": "input",
                    "config": {
                        "fields": [
                            {"name": "tender_doc", "type": "text", "label": "招标文件内容"},
                            {"name": "rules", "type": "text", "label": "合规规则（可选）"},
                        ]
                    },
                },
                {
                    "id": "n2",
                    "type": "knowledge-retrieval",
                    "config": {
                        "query": "{{ input.tender_doc }}",
                        "top_k": 5,
                        "knowledge_base": "compliance",
                    },
                },
                {
                    "id": "n3",
                    "type": "llm",
                    "config": {
                        "prompt": (
                            "你是一个招标合规审查专家。请根据以下招标文件内容和检索到的相关法规条款，"
                            "进行合规性审查，指出不合规项及修改建议。\n\n"
                            "【招标文件】\n{{ input.tender_doc }}\n\n"
                            "【相关法规】\n{{ n2.output }}\n\n"
                            "请输出审查结论。"
                        ),
                        "model": "deepseek-chat",
                    },
                },
                {
                    "id": "n4",
                    "type": "output",
                    "config": {
                        "variables": [
                            {"name": "review_result", "source": "n3.output"},
                            {"name": "retrieved_rules", "source": "n2.output"},
                        ]
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n3", "target": "n4"},
            ],
        },
    },
    {
        "name": "围串标分析",
        "description": "分析投标文件中的围标、串标嫌疑特征，包括IP雷同、文件属性雷同、报价规律等，输出风险分析报告。",
        "category": "collusion",
        "icon": "TeamOutlined",
        "sort_order": 2,
        "is_builtin": True,
        "dag_definition": {
            "nodes": [
                {
                    "id": "n1",
                    "type": "input",
                    "config": {
                        "fields": [
                            {"name": "bid_files", "type": "text", "label": "投标文件数据"},
                            {"name": "threshold", "type": "number", "label": "相似度阈值", "default": 0.8},
                        ]
                    },
                },
                {
                    "id": "n2",
                    "type": "code",
                    "config": {
                        "code": (
                            "import json\n"
                            "data = input.get('bid_files', [])\n"
                            "threshold = float(input.get('threshold', 0.8))\n"
                            "# 模拟分析：检查IP、文件属性、报价规律等\n"
                            "result = {\n"
                            '    "ip_duplicates": [],\n'
                            '    "similar_docs": [],\n'
                            '    "price_anomalies": [],\n'
                            '    "risk_level": "low",\n'
                            "}\n"
                            "output = json.dumps(result, ensure_ascii=False)"
                        ),
                        "language": "python",
                    },
                },
                {
                    "id": "n3",
                    "type": "llm",
                    "config": {
                        "prompt": (
                            "你是一个招投标反舞弊分析专家。以下是投标文件的分析数据：\n\n"
                            "{{ n2.output }}\n\n"
                            "请根据分析数据判断是否存在围标串标嫌疑，输出风险等级和建议。"
                        ),
                        "model": "deepseek-chat",
                    },
                },
                {
                    "id": "n4",
                    "type": "output",
                    "config": {
                        "variables": [
                            {"name": "analysis", "source": "n3.output"},
                            {"name": "raw_data", "source": "n2.output"},
                        ]
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n3", "target": "n4"},
            ],
        },
    },
    {
        "name": "纪检模拟谈话",
        "description": "模拟纪检谈话场景，AI 扮演谈话人，根据预设规则与被谈话人进行交互式对话，用于纪检监察培训与演练。",
        "category": "interview",
        "icon": "CustomerServiceOutlined",
        "sort_order": 3,
        "is_builtin": True,
        "dag_definition": {
            "nodes": [
                {
                    "id": "n1",
                    "type": "input",
                    "config": {
                        "fields": [
                            {"name": "scenario", "type": "text", "label": "谈话场景设定"},
                            {"name": "subject_info", "type": "text", "label": "被谈话人信息"},
                        ]
                    },
                },
                {
                    "id": "n2",
                    "type": "agent",
                    "config": {
                        "system_prompt": (
                            "你是纪委谈话人，正在与被谈话人进行纪律审查谈话。\n"
                            "谈话场景：{{ input.scenario }}\n"
                            "被谈话人信息：{{ input.subject_info }}\n\n"
                            "规则：1）保持专业、严肃的谈话风格；2）根据被谈话人的回答动态调整追问方向；"
                            "3）不得泄露未掌握的线索信息；4）每次只提一个问题，等待回答。"
                        ),
                        "model": "deepseek-chat",
                        "max_turns": 20,
                        "mode": "chat",
                    },
                },
                {
                    "id": "n3",
                    "type": "output",
                    "config": {
                        "variables": [
                            {"name": "conversation_log", "source": "n2.output"},
                        ]
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        },
    },
    {
        "name": "AI 问数",
        "description": "通过自然语言提问，由 AI 自动理解问题并查询数据，返回分析结果。适用于快速数据查询与分析场景。",
        "category": "chat",
        "icon": "SearchOutlined",
        "sort_order": 4,
        "is_builtin": True,
        "dag_definition": {
            "nodes": [
                {
                    "id": "n1",
                    "type": "input",
                    "config": {
                        "fields": [
                            {"name": "question", "type": "text", "label": "请输入您的问题"},
                        ]
                    },
                },
                {
                    "id": "n2",
                    "type": "llm",
                    "config": {
                        "prompt": (
                            "你是一个数据分析助手。请回答以下问题：\n\n"
                            "{{ input.question }}\n\n"
                            "如果问题涉及数据查询，请说明需要查询的数据源和查询条件。"
                        ),
                        "model": "deepseek-chat",
                    },
                },
                {
                    "id": "n3",
                    "type": "output",
                    "config": {
                        "variables": [
                            {"name": "answer", "source": "n2.output"},
                        ]
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        },
    },
    {
        "name": "AI问数(Excel)",
        "description": "上传 Excel/CSV 文件，用自然语言提问，AI 自动分析数据返回结果。",
        "category": "analysis",
        "icon": "TableOutlined",
        "sort_order": 5,
        "is_builtin": True,
        "dag_definition": {
            "nodes": [
                {"id": "n1", "type": "input", "config": {"fields": [{"name": "question", "type": "text", "label": "请输入问题"}, {"name": "file_path", "type": "text", "label": "文件路径"}]}},
                {"id": "n2", "type": "excel-parser", "config": {"file_path": "{{ input.file_path }}", "max_rows": 100}},
                {"id": "n3", "type": "llm", "config": {"model": "deepseek-chat", "system_prompt": "你是数据分析助手。以下是Excel数据：\n{{ n2.data_text }}\n\n概况: {{ n2.summary }}", "prompt": "{{ input.question }}\n\n请基于以上数据进行分析。"}},
                {"id": "n4", "type": "output", "config": {"variables": [{"name": "analysis", "source": "n3.output"}, {"name": "summary", "source": "n2.summary"}]}}
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n3", "target": "n4"}
            ]
        }
    },
]


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取模板列表（含内置模板）"""
    # 从数据库获取用户自定义模板
    result = await db.execute(
        select(WorkflowTemplate).order_by(WorkflowTemplate.sort_order)
    )
    custom_templates = result.scalars().all()

    # 将内置模板转换为响应格式
    builtin_responses = [
        TemplateResponse(
            id=f"builtin_{t['name']}",
            name=t["name"],
            description=t["description"],
            category=t["category"],
            dag_definition=t["dag_definition"],
            icon=t["icon"],
            sort_order=t["sort_order"],
            is_builtin=True,
            created_at="",
        )
        for t in BUILTIN_TEMPLATES
    ]

    custom_responses = [
        TemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description or "",
            category=t.category,
            dag_definition=t.dag_definition,
            icon=t.icon or "",
            sort_order=t.sort_order,
            is_builtin=t.is_builtin,
            created_at=t.created_at.isoformat() if t.created_at else "",
        )
        for t in custom_templates
    ]

    # 合并：内置模板优先，按 sort_order 排序
    combined = sorted(
        builtin_responses + custom_responses,
        key=lambda x: (x.sort_order, x.name),
    )
    return combined


@router.post("/{template_id}/instantiate", response_model=TemplateInstantiateResponse)
async def instantiate_template(
    template_id: str,
    body: TemplateInstantiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从模板创建工作流"""
    dag_definition = None
    template_name = ""

    # 检查是否是内置模板
    for t in BUILTIN_TEMPLATES:
        if template_id == f"builtin_{t['name']}":
            dag_definition = _ensure_node_positions(t["dag_definition"])
            template_name = t["name"]
            break

    # 检查数据库模板
    if dag_definition is None:
        try:
            tpl_uuid = uuid.UUID(template_id)
        except (ValueError, AttributeError):
            raise HTTPException(status_code=404, detail="模板不存在")
        result = await db.execute(
            select(WorkflowTemplate).where(WorkflowTemplate.id == tpl_uuid)
        )
        tpl = result.scalar_one_or_none()
        if not tpl:
            raise HTTPException(status_code=404, detail="模板不存在")
        dag_definition = _ensure_node_positions(tpl.dag_definition)
        template_name = tpl.name

    # 创建工作流
    wf_name = body.name or f"{template_name}（从模板创建）"
    wf = Workflow(
        tenant_id=current_user.tenant_id,
        name=wf_name,
        description=body.description or f"从模板「{template_name}」创建",
        type="chatflow" if template_name in ("纪检模拟谈话",) else "workflow",
        dag_definition=dag_definition,
        created_by=current_user.id,
    )
    db.add(wf)
    await db.flush()

    return TemplateInstantiateResponse(
        workflow_id=str(wf.id),
        workflow_name=wf.name,
    )
