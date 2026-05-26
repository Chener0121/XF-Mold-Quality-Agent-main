from sqlalchemy import select, func as sa_func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.entities.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Conversation CRUD ──

    async def create_conversation(self, conv: Conversation) -> Conversation:
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def get_conversation(self, conv_id: str) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conv_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[Conversation], int]:
        count_stmt = select(sa_func.count()).select_from(Conversation)
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def update_title(self, conv_id: str, title: str) -> None:
        conv = await self.get_conversation(conv_id)
        if conv:
            conv.title = title

    async def delete_conversation(self, conv_id: str) -> None:
        conv = await self.get_conversation(conv_id)
        if conv:
            await self.session.delete(conv)

    # ── Messages ──

    async def add_message(self, msg: Message) -> Message:
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_history(
        self, conversation_id: str, limit: int = 20,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))
