"""Embedding 输出模型"""

from typing import Any

from pydantic import BaseModel, Field


class EmbeddedBlock(BaseModel):
    """向量化后的语义块，用于存入 Chroma"""

    id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
