from fastapi import APIRouter

from src.models.schemas.chat import ChatRequest, ChatResponse, SourceItem
from src.services.document_service import DocumentService

router = APIRouter()

_service: DocumentService | None = None


def _get_service() -> DocumentService:
    global _service
    if _service is None:
        _service = DocumentService()
    return _service


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """智能问答接口 — 语义检索"""
    service = _get_service()
    hits = service.search(request.question, top_k=5)

    sources = [
        SourceItem(
            document_id=h.get("id", ""),
            chunk_id="",
            content=h.get("content", ""),
            score=1.0 - (h.get("distance") or 0),
        )
        for h in hits
    ]

    # 拼接检索到的上下文作为回答
    context_parts = [s.content for s in sources if s.content]
    answer = "\n\n---\n\n".join(context_parts) if context_parts else "未找到相关内容"

    return ChatResponse(answer=answer, sources=sources)
