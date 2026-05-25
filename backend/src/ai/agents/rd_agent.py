"""R&D Agent — 研发领域专用的 RAG Agent"""

from src.ai.rag.retrievers.context_builder import ContextBuilder
from src.ai.rag.retrievers.retriever import Retriever
from src.ai.rag.retrievers.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE
from src.core.llm_client import get_chat_llm
from src.core.logger import get_logger

logger = get_logger(__name__)

DOMAIN = "rd"


class RDAgent:
    """研发 Agent：检索 R&D 领域知识库 + LLM 回答"""

    def __init__(self, retriever: Retriever | None = None):
        self.retriever = retriever or Retriever()
        self.builder = ContextBuilder()

    def ask(self, query: str, top_k: int = 5) -> dict:
        hits = self.retriever.retrieve(query, top_k=top_k, domain=DOMAIN)

        if not hits:
            return {"answer": "根据现有文档未找到相关信息。", "retrievals": []}

        context = self.builder.build(hits)

        llm = get_chat_llm()
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=RAG_USER_TEMPLATE.format(context=context, question=query)),
        ])
        answer = response.content if hasattr(response, "content") else str(response)

        return {
            "answer": answer,
            "retrievals": [
                {
                    "content": h.content[:300],
                    "score": h.score,
                    "source": h.metadata.get("source", ""),
                    "section_title": h.metadata.get("section_title", ""),
                    "primary_domain": h.metadata.get("primary_domain", ""),
                }
                for h in hits
            ],
        }
