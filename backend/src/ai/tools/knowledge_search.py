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


def _do_search(query: str, top_k: int, domain: str | None) -> str:
    retriever = _get_retriever()
    builder = _get_builder()

    hits = retriever.retrieve(query=query, top_k=top_k, domain=domain)

    if not hits:
        return "未找到相关文档片段。请尝试不同的查询词。"

    context = builder.build(hits)
    logger.info("search: query=%r, domain=%s, top_k=%d, hits=%d", query[:50], domain, top_k, len(hits))
    return context


class _SearchInput(BaseModel):
    query: str = Field(description="检索查询词")
    top_k: int = Field(default=5, description="返回结果数量")


class _QualitySearchInput(BaseModel):
    query: str = Field(description="检索查询词")
    top_k: int = Field(default=8, description="返回结果数量")


@tool(args_schema=_QualitySearchInput)
def quality_search(query: str, top_k: int = 8) -> str:
    """搜索质量管理知识库（FMEA 手册、VDA6.4 质量手册等）。
    需要时可用不同的关键词多次调用。"""
    return _do_search(query, top_k=top_k, domain="quality")


@tool(args_schema=_SearchInput)
def rd_search(query: str, top_k: int = 5) -> str:
    """搜索研发知识库（模具设计规范、工艺开发文档等）。
    需要时可用不同的关键词多次调用。"""
    return _do_search(query, top_k=top_k, domain="rd")


@tool(args_schema=_SearchInput)
def general_search(query: str, top_k: int = 5) -> str:
    """搜索全部知识库（质量管理和研发文档）。
    需要时可用不同的关键词多次调用。"""
    return _do_search(query, top_k=top_k, domain=None)
