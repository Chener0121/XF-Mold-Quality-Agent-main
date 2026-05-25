from fastapi import APIRouter

from src.models.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """智能问答接口"""
    # TODO: 接入 RAG + Agent 流水线
    return ChatResponse(answer="暂未实现", sources=[])
