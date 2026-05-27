from sqlalchemy import String, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .document import Base


class AgentDocument(Base):
    __tablename__ = "agent_documents"
    __table_args__ = (PrimaryKeyConstraint("agent_name", "document_source"),)

    agent_name: Mapped[str] = mapped_column(String(50))
    document_source: Mapped[str] = mapped_column(String(255))
