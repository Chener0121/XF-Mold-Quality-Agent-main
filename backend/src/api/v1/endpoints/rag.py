from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.services.chat_service import ChatService
from src.models.schemas.rag import RAGQueryRequest, RAGQueryResponse, ToolCallItem

router = APIRouter()

_chat_service = ChatService()


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest, db: AsyncSession = Depends(get_db)):
    """Session-aware RAG 问答 pipeline"""
    result = await _chat_service.handle_query(
        query=request.query,
        conversation_id=request.conversation_id,
        db=db,
    )

    return RAGQueryResponse(
        answer=result["answer"],
        conversation_id=result["conversation_id"],
        domain=result["domain"],
        retrievals=[ToolCallItem(**tc) for tc in result["retrievals"]],
        context_preview=result["context_preview"],
        context_length=result["context_length"],
        rewritten_query=result.get("rewritten_query"),
    )
