from fastapi import APIRouter

from src.api.v1.endpoints import chat, document, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(chat.router, prefix="/chat", tags=["智能问答"])
api_router.include_router(document.router, prefix="/documents", tags=["文档管理"])
