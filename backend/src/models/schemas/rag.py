from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    domain: str | None = None  # quality / rd / None(全部)


class ToolCallItem(BaseModel):
    tool_name: str = ""
    content_preview: str = ""


class RAGQueryResponse(BaseModel):
    answer: str
    retrievals: list[ToolCallItem] = []
    context_preview: str = ""
    context_length: int = 0
