from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    """Request body for creating a new conversation."""

    workflow_id: str
    title: str = "New conversation"


class ConversationResponse(BaseModel):
    """Conversation summary returned in list / detail responses."""

    id: str
    workflow_id: str
    title: str
    status: str
    created_at: str
    updated_at: str


class MessageRequest(BaseModel):
    """Send a message (turn) in an existing conversation.

    ``content`` is the user's text.  ``inputs`` may contain additional
    key-value pairs that are merged into the workflow execution context.
    """

    content: str
    inputs: dict = {}


class MessageResponse(BaseModel):
    """A single message returned to the client."""

    id: str
    role: str
    content: str
    metadata: dict = {}
    created_at: str


class ChatResponse(BaseModel):
    """Full response to a message send: the assistant reply + final output."""

    message: MessageResponse
    output: dict = {}
    duration_ms: Optional[int] = None
