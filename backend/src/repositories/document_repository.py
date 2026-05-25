from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entities.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get_by_id(self, doc_id: str) -> Document | None:
        return await self.session.get(Document, doc_id)

    async def list_all(self, offset: int = 0, limit: int = 20) -> tuple[list[Document], int]:
        stmt = select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        count_stmt = select(func.count()).select_from(Document)
        total = (await self.session.execute(count_stmt)).scalar() or 0
        return list(result.scalars().all()), total

    async def delete(self, doc: Document) -> None:
        await self.session.delete(doc)
