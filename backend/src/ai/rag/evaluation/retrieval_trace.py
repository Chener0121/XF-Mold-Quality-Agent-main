"""RAG 检索追踪模型"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class RetrievalTrace(BaseModel):
    """单次 RAG 查询的完整追踪记录"""

    query: str
    top_k: int
    retrievals: list[dict[str, Any]] = Field(default_factory=list)
    final_context: str = ""
    context_length: int = 0
    answer: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
