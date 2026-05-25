from fastapi import APIRouter
from pydantic import BaseModel

from src.ai.rag.retrievers.context_builder import ContextBuilder
from src.ai.rag.retrievers.models import RetrievalResult
from src.ai.rag.retrievers.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE
from src.ai.rag.retrievers.retriever import Retriever
from src.core.llm_client import get_chat_llm

router = APIRouter()

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


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RAGSourceItem(BaseModel):
    block_id: str
    content: str
    score: float
    source: str = ""
    section_title: str = ""


class RAGQueryResponse(BaseModel):
    answer: str
    contexts: list[RAGSourceItem]


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """RAG 问答：检索知识库 + LLM 生成回答"""
    # 1. 检索
    retriever = _get_retriever()
    hits = retriever.retrieve(request.query, top_k=request.top_k)

    if not hits:
        return RAGQueryResponse(answer="根据现有文档未找到相关信息。", contexts=[])

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
    sources = [
        RAGSourceItem(
            block_id=h.block_id,
            content=h.content[:300],
            score=round(h.score, 4),
            source=h.metadata.get("source", ""),
            section_title=h.metadata.get("section_title", ""),
        )
        for h in hits
    ]

    return RAGQueryResponse(answer=answer, contexts=sources)
