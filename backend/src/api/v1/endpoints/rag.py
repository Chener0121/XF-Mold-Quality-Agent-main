from fastapi import APIRouter
from pydantic import BaseModel

from src.ai.rag.evaluation.retrieval_logger import RetrievalLogger
from src.ai.rag.evaluation.retrieval_trace import RetrievalTrace
from src.ai.rag.retrievers.context_builder import ContextBuilder
from src.ai.rag.retrievers.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE
from src.ai.rag.retrievers.retriever import Retriever
from src.core.llm_client import get_chat_llm

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


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RAGSourceItem(BaseModel):
    block_id: str
    content: str
    score: float
    source: str = ""
    section_title: str = ""
    heading_path: list[str] = []
    block_type: str = ""
    page: int | None = None


class RAGQueryResponse(BaseModel):
    answer: str
    retrievals: list[RAGSourceItem]
    context_preview: str = ""
    context_length: int = 0


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """RAG 问答：检索知识库 + LLM 生成回答，完整可观测"""
    # 1. 检索
    retriever = _get_retriever()
    hits = retriever.retrieve(request.query, top_k=request.top_k)

    if not hits:
        _get_trace_logger().log(RetrievalTrace(
            query=request.query, top_k=request.top_k,
            answer="根据现有文档未找到相关信息。",
        ))
        return RAGQueryResponse(
            answer="根据现有文档未找到相关信息。",
            retrievals=[], context_preview="", context_length=0,
        )

    # 2. 构建上下文
    builder = _get_builder()
    context = builder.build(hits)

    # 3. LLM 生成回答
    llm = get_chat_llm()
    from langchain_core.messages import SystemMessage, HumanMessage
    response = llm.invoke([
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=RAG_USER_TEMPLATE.format(context=context, question=request.query)),
    ])
    answer = response.content if hasattr(response, "content") else str(response)

    # 4. 组装结果
    retrievals = [
        RAGSourceItem(
            block_id=h.block_id,
            content=h.content[:300],
            score=round(h.score, 4),
            source=h.metadata.get("source", ""),
            section_title=h.metadata.get("section_title", ""),
            heading_path=str(h.metadata.get("heading_path", "")).split(" > ") if h.metadata.get("heading_path") else [],
            block_type=h.metadata.get("type", ""),
            page=h.metadata.get("page"),
        )
        for h in hits
    ]

    # 5. 记录 trace
    trace = RetrievalTrace(
        query=request.query,
        top_k=request.top_k,
        retrievals=[r.model_dump() for r in retrievals],
        final_context=context,
        context_length=len(context),
        answer=answer,
    )
    _get_trace_logger().log(trace)

    return RAGQueryResponse(
        answer=answer,
        retrievals=retrievals,
        context_preview=context[:500],
        context_length=len(context),
    )
