from pydantic import BaseModel

from src.models.schemas.conversation import ToolCallItem


class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    agent: str | None = None
    rules: str | None = None


class RAGQueryResponse(BaseModel):
    answer: str
    conversation_id: str
    domain: str = ""
    retrievals: list[ToolCallItem] = []
    context_preview: str = ""
    context_length: int = 0
    rewritten_query: str | None = None
