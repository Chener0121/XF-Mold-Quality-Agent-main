"""Chat Service — conversation orchestration + message persistence"""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.chat.query_pipeline import process, PipelineResult
from src.models.entities.conversation import Conversation, Message
from src.repositories.conversation_repository import ConversationRepository
from src.core.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """编排会话生命周期：创建/加载会话 → 调用 pipeline → 持久化消息"""

    async def handle_query(
        self,
        query: str,
        conversation_id: str | None,
        db: AsyncSession,
    ) -> dict:
        repo = ConversationRepository(db)

        # 1. 加载或创建 conversation
        if conversation_id:
            conv = await repo.get_conversation(conversation_id)
            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")
        else:
            conv = Conversation(title="新对话")
            await repo.create_conversation(conv)
            conversation_id = conv.id

        # 2. 保存 user message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=query,
        )
        await repo.add_message(user_msg)

        # 3. 加载 history
        history = await repo.get_history(conversation_id, limit=20)

        # 4. 调用 pipeline
        result: PipelineResult = await process(query, history)

        # 5. 保存 assistant message
        retrievals_json = json.dumps(result.tool_calls, ensure_ascii=False)
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=result.answer,
            retrievals_json=retrievals_json,
        )
        await repo.add_message(assistant_msg)

        # 6. 更新 title（首次对话）
        if conv.title == "新对话":
            conv.title = query[:20] + ("..." if len(query) > 20 else "")

        logger.info(
            "Query handled: conv=%s, domain=%s, rewritten=%s",
            conversation_id[:8], result.domain,
            "yes" if result.rewritten_query != query else "no",
        )

        return {
            "answer": result.answer,
            "conversation_id": conversation_id,
            "domain": result.domain,
            "retrievals": result.tool_calls,
            "context_preview": "\n---\n".join(
                tc.get("content_preview", "") for tc in result.tool_calls
            ),
            "context_length": sum(
                len(tc.get("content_preview", "")) for tc in result.tool_calls
            ),
            "rewritten_query": (
                result.rewritten_query if result.rewritten_query != query else None
            ),
        }
