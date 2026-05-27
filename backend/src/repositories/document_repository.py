from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entities.document import Document
from src.models.entities.agent_document import AgentDocument


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

    # ── Agent-Document 关联（用 document source/filename 作为标识）──

    async def get_agent_documents(self, agent: str) -> list[str]:
        """返回该智能体关联的文档 source（filename）列表"""
        stmt = select(AgentDocument.document_source).where(AgentDocument.agent_name == agent)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def set_agent_documents(self, agent: str, sources: list[str]) -> None:
        """设置该智能体的文档（全量替换）"""
        await self.session.execute(
            delete(AgentDocument).where(AgentDocument.agent_name == agent),
        )
        for source in sources:
            self.session.add(AgentDocument(agent_name=agent, document_source=source))
        await self.session.flush()
