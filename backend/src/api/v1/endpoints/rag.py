from fastapi import APIRouter

from src.ai.agents.rag_agent import ask as agent_ask
from src.ai.rag.evaluation.retrieval_logger import RetrievalLogger
from src.ai.rag.evaluation.retrieval_trace import RetrievalTrace
from src.models.schemas.rag import RAGQueryRequest, RAGQueryResponse, ToolCallItem

router = APIRouter()

_trace_logger: RetrievalLogger | None = None


def _get_trace_logger() -> RetrievalLogger:
    global _trace_logger
    if _trace_logger is None:
        _trace_logger = RetrievalLogger()
    return _trace_logger


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """RAG 问答：LangGraph Agent 自动检索 + LLM 生成回答"""
    result = agent_ask(request.query, domain=request.domain)

    tool_calls = result.get("tool_calls", [])
    retrievals = [ToolCallItem(**tc) for tc in tool_calls]
    context_preview = "\n---\n".join(tc["content_preview"] for tc in tool_calls)

    _get_trace_logger().log(RetrievalTrace(
        query=request.query,
        top_k=request.top_k,
        retrievals=tool_calls,
        final_context=context_preview,
        context_length=len(context_preview),
        answer=result["answer"],
    ))

    return RAGQueryResponse(
        answer=result["answer"],
        retrievals=retrievals,
        context_preview=context_preview,
        context_length=len(context_preview),
    )
