import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageRequest,
    MessageResponse,
    ChatResponse,
)
from app.engine.dag import WorkflowDag
from app.engine.executor import WorkflowExecutor
from app.engine.chat_context import ChatExecutionContext
from app.nodes import NODE_REGISTRY

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ---------------------------------------------------------------------------
# Conversation CRUD
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=ConversationResponse)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat conversation bound to a workflow."""
    # Verify the workflow exists and belongs to the tenant
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == uuid.UUID(body.workflow_id),
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    conv = Conversation(
        workflow_id=wf.id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        title=body.title,
    )
    db.add(conv)
    await db.flush()
    return ConversationResponse(
        id=str(conv.id),
        workflow_id=str(conv.workflow_id),
        title=conv.title or "",
        status=conv.status,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversations for the current tenant."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.tenant_id == current_user.tenant_id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [
        ConversationResponse(
            id=str(c.id),
            workflow_id=str(c.workflow_id),
            title=c.title or "",
            status=c.status,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in convs
    ]


# ---------------------------------------------------------------------------
# Messages — multi-turn chat
# ---------------------------------------------------------------------------


@router.post("/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    body: MessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a user message and get the assistant reply.

    The message is recorded as a ``user``-role message in the conversation
    history, then the bound workflow is executed.  The workflow output is
    stored as an ``assistant``-role message, and conversation variables
    are persisted for the next turn.
    """
    # ------------------------------------------------------------------
    # 1. Load conversation
    # ------------------------------------------------------------------
    conv_id = uuid.UUID(conversation_id)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.tenant_id == current_user.tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.status == "closed":
        raise HTTPException(status_code=400, detail="对话已关闭")

    # ------------------------------------------------------------------
    # 2. Load workflow
    # ------------------------------------------------------------------
    wf_result = await db.execute(
        select(Workflow).where(
            Workflow.id == conv.workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
    )
    wf = wf_result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="关联的工作流不存在")

    # ------------------------------------------------------------------
    # 3. Record the user message
    # ------------------------------------------------------------------
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)

    # ------------------------------------------------------------------
    # 4. Build the execution context with history & persisted variables
    # ------------------------------------------------------------------
    dag = WorkflowDag(
        nodes=wf.dag_definition.get("nodes", []),
        edges=wf.dag_definition.get("edges", []),
    )

    # Fetch all prior messages for history context
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    all_messages = history_result.scalars().all()
    history_list = [{"role": m.role, "content": m.content} for m in all_messages]

    # Merge the user's message text and extra inputs
    exec_inputs = {"message": body.content, **body.inputs}

    chat_ctx = ChatExecutionContext(
        inputs=exec_inputs,
        db=db,
        tenant_id=current_user.tenant_id,
        conversation=conv,
        history=history_list,
    )

    # ------------------------------------------------------------------
    # 5. Execute the workflow
    # ------------------------------------------------------------------
    executor = WorkflowExecutor(dag, NODE_REGISTRY, db=db, tenant_id=current_user.tenant_id)

    start_time = time.time()
    try:
        output = executor.execute(inputs=exec_inputs, context=chat_ctx)
        duration = int((time.time() - start_time) * 1000)
        status_val = "success"
        error_text = None
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        output = {}
        status_val = "failed"
        error_text = str(e)

    # ------------------------------------------------------------------
    # 6. Persist conversation context
    # ------------------------------------------------------------------
    persisted = chat_ctx.get_persistable_outputs()
    conv.variables = persisted
    conv.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )

    # ------------------------------------------------------------------
    # 7. Record the assistant message
    # ------------------------------------------------------------------
    assistant_content = (
        str(output) if output else (error_text or "处理完成")
    )
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=assistant_content,
        extra_data={"output": output, "error": error_text} if error_text else {"output": output},
    )
    db.add(assistant_msg)
    await db.flush()

    if status_val == "failed":
        raise HTTPException(status_code=500, detail=error_text)

    return ChatResponse(
        message=MessageResponse(
            id=str(assistant_msg.id),
            role=assistant_msg.role,
            content=assistant_msg.content,
            metadata=assistant_msg.extra_data or {},
            created_at=assistant_msg.created_at.isoformat(),
        ),
        output=output,
        duration_ms=duration,
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full message history for a conversation."""
    conv_id = uuid.UUID(conversation_id)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.tenant_id == current_user.tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()
    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            metadata=m.extra_data or {},
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]
