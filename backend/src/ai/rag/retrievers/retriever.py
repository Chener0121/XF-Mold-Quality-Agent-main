"""语义检索器 — query → embedding → Chroma search → RetrievalResult"""

from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.retrievers.models import RetrievalResult
from src.ai.rag.vectorstores.chroma_store import ChromaStore
from src.core.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    def __init__(self, store: ChromaStore | None = None, embedder: Embedder | None = None):
        self.store = store or ChromaStore()
        self.embedder = embedder or Embedder()

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """对 query 做 embedding，检索 Chroma，返回统一结果"""
        query_embedding = self.embedder.embed([query])[0]

        results = self.store.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[RetrievalResult] = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0
            hits.append(RetrievalResult(
                block_id=doc_id,
                content=results["documents"][0][i] if results["documents"] else "",
                score=1.0 - distance,
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
            ))

        logger.info("检索完成: query=%r, top_k=%d, hits=%d", query[:50], top_k, len(hits))
        return hits
