from datetime import datetime

from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: str | None = None


class ToolCallItem(BaseModel):
    tool_name: str = ""
    content_preview: str = ""


class RAGQueryResponse(BaseModel):
    answer: str
    conversation_id: str
    domain: str = ""
    retrievals: list[ToolCallItem] = []
    context_preview: str = ""
    context_length: int = 0
    rewritten_query: str | None = None


# ── Conversation Schemas ──

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime | None = None


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    retrievals: list[ToolCallItem] = []
    created_at: datetime | None = None


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    messages: list[MessageResponse]
    created_at: datetime | None = None
