from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    domain: str | None = None  # quality / rd / None(全部)


class RAGSourceItem(BaseModel):
    block_id: str
    content: str
    score: float
    source: str = ""
    section_title: str = ""
    heading_path: list[str] = []
    block_type: str = ""
    page: int | None = None
    primary_domain: str = ""


class RAGQueryResponse(BaseModel):
    answer: str
    retrievals: list[RAGSourceItem]
    context_preview: str = ""
    context_length: int = 0
