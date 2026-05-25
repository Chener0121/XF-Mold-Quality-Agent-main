"""统一语义块 — 系统核心知识单元"""

from pydantic import BaseModel, Field


class SemanticBlock(BaseModel):
    """
    所有文档元素最终统一转换为 SemanticBlock。

    无论来源是文本、表格、流程图、乌龟图、截图，
    都通过此结构进入 embedding / retrieval / RAG / Agent。
    """

    type: str
    content: str
    summary: str = ""
    keywords: list[str] = Field(default_factory=list)
    source: str = ""
    index: int = 0
    page: int | None = None
    metadata: dict = Field(default_factory=dict)
