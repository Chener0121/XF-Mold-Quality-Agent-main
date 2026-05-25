from fastapi import APIRouter
from pydantic import BaseModel

from src.ai.agents.quality_agent import QualityAgent
from src.ai.agents.rd_agent import RDAgent
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
_quality_agent: QualityAgent | None = None
_rd_agent: RDAgent | None = None


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


def _get_quality_agent() -> QualityAgent:
    global _quality_agent
    if _quality_agent is None:
        _quality_agent = QualityAgent()
    return _quality_agent


def _get_rd_agent() -> RDAgent:
    global _rd_agent
    if _rd_agent is None:
        _rd_agent = RDAgent()
    return _rd_agent


# ── 通用 RAG ──

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

    llm = get_chat_llm()
    from langchain_core.messages import SystemMessage, HumanMessage
    response = llm.invoke([
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=RAG_USER_TEMPLATE.format(context=context, question=request.query)),
    ])
    answer = response.content if hasattr(response, "content") else str(response)

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


# ── Agent 专用接口 ──

class AgentQueryRequest(BaseModel):
    query: str


class AgentQueryResponse(BaseModel):
    answer: str
    retrievals: list[dict]


@router.post("/quality", response_model=AgentQueryResponse)
async def quality_agent_query(request: AgentQueryRequest):
    """Quality Agent：质量管理领域专用问答"""
    agent = _get_quality_agent()
    result = agent.ask(request.query)
    return AgentQueryResponse(**result)


@router.post("/rd", response_model=AgentQueryResponse)
async def rd_agent_query(request: AgentQueryRequest):
    """R&D Agent：研发领域专用问答"""
    agent = _get_rd_agent()
    result = agent.ask(request.query)
    return AgentQueryResponse(**result)
