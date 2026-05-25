from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class SourceItem(BaseModel):
    document_id: str
    chunk_id: str
    content: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
