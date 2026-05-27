import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.core.dependencies import async_session_factory
from src.ai.chat.query_pipeline import process_stream
from src.models.entities.conversation import Conversation, Message
from src.models.schemas.rag import RAGQueryRequest
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.document_repository import DocumentRepository
from src.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _sse_event(event: str, data: dict) -> str:
    """格式化 SSE 事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("")
async def rag_query_stream(request: RAGQueryRequest):
    """SSE 流式 RAG 问答"""

    async def event_generator():
        async with async_session_factory() as db:
            try:
                repo = ConversationRepository(db)

                # 1. 加载或创建 conversation
                if request.conversation_id:
                    conv = await repo.get_conversation(request.conversation_id)
                    if not conv:
                        yield _sse_event("error", {"message": "会话不存在"})
                        return
                    conversation_id = request.conversation_id
                else:
                    conv = Conversation(title="新对话")
                    await repo.create_conversation(conv)
                    conversation_id = conv.id

                # 2. 保存 user message 并 commit
                user_msg = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=request.query,
                )
                await repo.add_message(user_msg)
                await db.commit()

                # 3. 加载 history
                history = await repo.get_history(conversation_id, limit=20)

                # 4. 查询智能体关联的文档（source/filename 用于 ChromaDB 过滤）
                document_sources: list[str] | None = None
                agent = request.agent or "general"
                if agent != "general":
                    doc_repo = DocumentRepository(db)
                    document_sources = await doc_repo.get_agent_documents(agent)

                # 5. 流式 pipeline
                full_answer = ""
                thinking_content = ""
                tool_calls: list[dict] = []
                token_count = 0

                logger.info("SSE stream started: conv=%s", conversation_id[:8])

                async for event_type, data in process_stream(
                    request.query, history, agent=agent, document_ids=document_sources,
                    rules=request.rules,
                ):
                    if event_type == "meta":
                        data["conversation_id"] = conversation_id
                    elif event_type == "thinking":
                        thinking_content += data["content"]
                    elif event_type == "token":
                        full_answer += data["content"]
                        token_count += 1
                    elif event_type == "done":
                        tool_calls = data.get("tool_calls", [])
                    yield _sse_event(event_type, data)

                logger.info("SSE stream done: tokens=%d, answer_len=%d", token_count, len(full_answer))

                # 5. 保存 assistant message
                retrievals_json = json.dumps(tool_calls, ensure_ascii=False)
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_answer,
                    retrievals_json=retrievals_json,
                )
                await repo.add_message(assistant_msg)

                # 6. 更新 title
                if conv.title == "新对话":
                    conv.title = request.query[:20] + ("..." if len(request.query) > 20 else "")

                await db.commit()

            except Exception as e:
                logger.error("Stream error: %s", e, exc_info=True)
                yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
