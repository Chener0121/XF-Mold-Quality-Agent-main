from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    agent: str | None = None
    rules: str | None = None
