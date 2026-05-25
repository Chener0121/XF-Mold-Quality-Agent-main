"""知识库检索工具 — 供 LangGraph Agent 调用"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.ai.rag.retrievers.context_builder import ContextBuilder
from src.ai.rag.retrievers.retriever import Retriever
from src.core.logger import get_logger

logger = get_logger(__name__)

_retriever: Retriever | None = None
_builder: ContextBuilder | None = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _get_builder() -> ContextBuilder:
    global _builder
    if _builder is None:
        _builder = ContextBuilder()
    return _builder


class KnowledgeSearchInput(BaseModel):
    query: str = Field(description="检索查询词")
    top_k: int = Field(default=5, description="返回结果数量")
    domain: str | None = Field(
        default=None,
        description="领域过滤: 'quality'(质量管理) 或 'rd'(研发)。不传则搜索全部领域。",
    )


@tool(args_schema=KnowledgeSearchInput)
def knowledge_search(query: str, top_k: int = 5, domain: str | None = None) -> str:
    """搜索 XF 模具质量知识库。可检索 FMEA 手册、VDA6.4 质量手册及研发文档。
    需要时可用不同的关键词多次调用。"""
    retriever = _get_retriever()
    builder = _get_builder()

    hits = retriever.retrieve(query=query, top_k=top_k, domain=domain)

    if not hits:
        return "未找到相关文档片段。请尝试不同的查询词或移除领域过滤。"

    context = builder.build(hits)
    logger.info("knowledge_search: query=%r, domain=%s, hits=%d", query[:50], domain, len(hits))
    return context
