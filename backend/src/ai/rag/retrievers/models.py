"""检索结果模型"""

from typing import Any

from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    block_id: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
