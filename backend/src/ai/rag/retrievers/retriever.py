"""语义检索器 — 支持领域过滤和 score boosting"""

from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.retrievers.models import RetrievalResult
from src.ai.rag.vectorstores.chroma_store import ChromaStore
from src.core.logger import get_logger

logger = get_logger(__name__)

DOMAIN_BOOST = 0.05  # primary_domain 匹配时的加分


class Retriever:
    def __init__(self, store: ChromaStore | None = None, embedder: Embedder | None = None):
        self.store = store or ChromaStore()
        self.embedder = embedder or Embedder()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RetrievalResult]:
        """检索 + 可选领域过滤 + score boosting"""
        query_embedding = self.embedder.embed([query])[0]

        # 领域过滤：多取一些候选，boost 后再截取
        fetch_k = top_k * 3 if domain else top_k

        where_filter = None
        if domain:
            where_filter = {"domains": {"$contains": domain}}

        results = self.store.collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[RetrievalResult] = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0
            score = 1.0 - distance
            meta = results["metadatas"][0][i] if results["metadatas"] else {}

            # Score boosting: primary_domain 匹配时加分
            if domain and meta.get("primary_domain") == domain:
                score += DOMAIN_BOOST

            hits.append(RetrievalResult(
                block_id=doc_id,
                content=results["documents"][0][i] if results["documents"] else "",
                score=round(score, 6),
                metadata=meta,
            ))

        # 按 score 排序后截取 top_k
        hits.sort(key=lambda x: x.score, reverse=True)
        hits = hits[:top_k]

        logger.info("检索完成: query=%r, domain=%s, top_k=%d, hits=%d", query[:50], domain, top_k, len(hits))
        return hits
