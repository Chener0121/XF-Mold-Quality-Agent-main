from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entities.agent_document import AgentDocument


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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
