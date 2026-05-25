from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entities.chunk import Chunk


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, chunks: list[Chunk]) -> None:
        self.session.add_all(chunks)
        await self.session.flush()

    async def get_by_document_id(self, document_id: str) -> list[Chunk]:
        stmt = select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
