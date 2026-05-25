from fastapi import APIRouter

from src.ai.agents.base_agent import invoke_llm
from src.ai.rag.evaluation.retrieval_logger import RetrievalLogger
from src.ai.rag.evaluation.retrieval_trace import RetrievalTrace
from src.ai.rag.retrievers.context_builder import ContextBuilder
from src.ai.rag.retrievers.retriever import Retriever
from src.models.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSourceItem

router = APIRouter()

_retriever: Retriever | None = None
_builder: ContextBuilder | None = None
_trace_logger: RetrievalLogger | None = None


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


def _get_trace_logger() -> RetrievalLogger:
    global _trace_logger
    if _trace_logger is None:
        _trace_logger = RetrievalLogger()
    return _trace_logger


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """RAG 问答：检索知识库 + LLM 生成回答"""
    retriever = _get_retriever()
    hits = retriever.retrieve(request.query, top_k=request.top_k, domain=request.domain)

    if not hits:
        _get_trace_logger().log(RetrievalTrace(
            query=request.query, top_k=request.top_k,
            answer="根据现有文档未找到相关信息。",
        ))
        return RAGQueryResponse(
            answer="根据现有文档未找到相关信息。",
            retrievals=[], context_preview="", context_length=0,
        )

    context = _get_builder().build(hits)
    answer = invoke_llm(context, request.query)

    retrievals = [
        RAGSourceItem(
            block_id=h.block_id,
            content=h.content[:300],
            score=h.score,
            source=h.metadata.get("source", ""),
            section_title=h.metadata.get("section_title", ""),
            heading_path=str(h.metadata.get("heading_path", "")).split(" > ") if h.metadata.get("heading_path") else [],
            block_type=h.metadata.get("type", ""),
            page=h.metadata.get("page"),
            primary_domain=h.metadata.get("primary_domain", ""),
        )
        for h in hits
    ]

    trace = RetrievalTrace(
        query=request.query, top_k=request.top_k,
        retrievals=[r.model_dump() for r in retrievals],
        final_context=context, context_length=len(context), answer=answer,
    )
    _get_trace_logger().log(trace)

    return RAGQueryResponse(
        answer=answer, retrievals=retrievals,
        context_preview=context[:500], context_length=len(context),
    )
