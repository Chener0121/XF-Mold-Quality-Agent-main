"""混合检索器 — 向量检索 + BM25 + RRF 融合"""

from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.retrievers.bm25_index import BM25Index
from src.ai.rag.retrievers.models import RetrievalResult
from src.ai.rag.vectorstores.chroma_store import ChromaStore
from src.core.logger import get_logger

logger = get_logger(__name__)

DOMAIN_BOOST = 0.05
RRF_K = 60  # RRF 常数，越小单路排名影响越大
VECTOR_CANDIDATE_MULTIPLIER = 3  # 向量检索多取候选数


class Retriever:
    def __init__(self, store: ChromaStore | None = None, embedder: Embedder | None = None):
        self.store = store or ChromaStore()
        self.embedder = embedder or Embedder()
        self.bm25 = BM25Index(store=self.store)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RetrievalResult]:
        """向量检索 + BM25 混合检索，RRF 融合排序"""
        fetch_k = top_k * VECTOR_CANDIDATE_MULTIPLIER

        # ── 1. 向量检索 ──
        vector_hits = self._vector_search(query, fetch_k, domain)

        # ── 2. BM25 检索 ──
        bm25_hits = self.bm25.search(query, top_k=fetch_k)

        # ── 3. RRF 融合 ──
        merged = self._rrf_merge(vector_hits, bm25_hits, top_k, domain)

        logger.info(
            "混合检索完成: query=%r, domain=%s, vector=%d, bm25=%d, merged=%d",
            query[:50], domain, len(vector_hits), len(bm25_hits), len(merged),
        )
        return merged

    def _vector_search(
        self, query: str, fetch_k: int, domain: str | None,
    ) -> list[RetrievalResult]:
        query_embedding = self.embedder.embed([query])[0]

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

            if domain and meta.get("primary_domain") == domain:
                score += DOMAIN_BOOST

            hits.append(RetrievalResult(
                block_id=doc_id,
                content=results["documents"][0][i] if results["documents"] else "",
                score=round(score, 6),
                metadata=meta,
            ))
        return hits

    def _rrf_merge(
        self,
        vector_hits: list[RetrievalResult],
        bm25_hits: list[tuple[str, float]],
        top_k: int,
        domain: str | None,
    ) -> list[RetrievalResult]:
        """Reciprocal Rank Fusion: score = sum(1/(k + rank)) for each retrieval source"""
        rrf_scores: dict[str, float] = {}

        # 向量检索排名
        for rank, hit in enumerate(vector_hits):
            rrf_scores[hit.block_id] = rrf_scores.get(hit.block_id, 0) + 1.0 / (RRF_K + rank + 1)

        # BM25 排名
        for rank, (doc_id, _score) in enumerate(bm25_hits):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (RRF_K + rank + 1)

        # 按融合分数排序
        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]
        if not sorted_ids:
            return []

        # 构建 id → RetrievalResult 映射（优先用向量检索的结果，已有完整信息）
        vector_map = {h.block_id: h for h in vector_hits}

        # BM25 独有的结果需要从 Chroma 补充内容
        missing_ids = [bid for bid in sorted_ids if bid not in vector_map]
        missing_map = self._fetch_by_ids(missing_ids, domain)

        results = []
        for bid in sorted_ids:
            hit = vector_map.get(bid) or missing_map.get(bid)
            if hit:
                hit.score = round(rrf_scores[bid], 6)
                results.append(hit)

        return results

    def _fetch_by_ids(self, ids: list[str], domain: str | None) -> dict[str, RetrievalResult]:
        """根据 id 列表从 Chroma 补充完整信息"""
        if not ids:
            return {}

        results = self.store.collection.get(ids=ids, include=["documents", "metadatas"])
        hits: dict[str, RetrievalResult] = {}

        for i, doc_id in enumerate(results["ids"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            hits[doc_id] = RetrievalResult(
                block_id=doc_id,
                content=results["documents"][i] if results["documents"] else "",
                score=0.0,
                metadata=meta,
            )
        return hits
