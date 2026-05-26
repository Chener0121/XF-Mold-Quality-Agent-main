import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.repositories.conversation_repository import ConversationRepository
from src.models.schemas.rag import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
    ToolCallItem,
)

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conversations, total = await repo.list_conversations(offset=offset, limit=limit)
    return ConversationListResponse(
        items=[
            ConversationResponse(id=c.id, title=c.title, created_at=c.created_at)
            for c in conversations
        ],
        total=total,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = []
    for msg in conv.messages:
        retrievals = []
        if msg.retrievals_json:
            try:
                raw = json.loads(msg.retrievals_json)
                retrievals = [ToolCallItem(**tc) for tc in raw]
            except (json.JSONDecodeError, TypeError):
                pass

        messages.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            retrievals=retrievals,
            created_at=msg.created_at,
        ))

    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        messages=messages,
        created_at=conv.created_at,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    await repo.delete_conversation(conversation_id)
