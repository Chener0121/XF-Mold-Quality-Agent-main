"""检索评测 — 对比纯向量检索 vs 混合检索 (Vector + BM25 + RRF)

用法:
    cd /app
    uv run python -m tests.generate_eval_dataset   # 先生成数据集
    uv run python -m tests.run_retrieval_eval       # 运行评测
"""

import json
from pathlib import Path

import chromadb
import jieba
from rank_bm25 import BM25Okapi

from src.ai.rag.embeddings.embedder import Embedder
from src.core.config import settings

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"
TOP_K = 5
RRF_K = 60
VECTOR_CANDIDATE_MULTIPLIER = 3


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    hits = set(retrieved_ids[:k]) & set(relevant_ids)
    return len(hits) / len(relevant_ids) if relevant_ids else 0.0


def mrr(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    return 1.0 if set(retrieved_ids[:k]) & set(relevant_ids) else 0.0


def fmt(val: float) -> str:
    return f"{val:.2%}"


def _tokenize(text: str) -> list[str]:
    return [w for w in jieba.cut(text) if w.strip()]


class EvalRetriever:
    """独立检索器，绕过项目 __init__.py 循环导入"""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(
            name="semantic_blocks",
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = Embedder()
        self._bm25: BM25Okapi | None = None
        self._ids: list[str] = []
        self._contents: list[str] = []
        self._build_bm25()

    def _build_bm25(self):
        data = self.collection.get(include=["documents"])
        self._ids = data["ids"]
        self._contents = data["documents"] or [""] * len(self._ids)
        tokenized = [_tokenize(doc) for doc in self._contents]
        self._bm25 = BM25Okapi(tokenized)

    def vector_search(self, query: str, top_k: int) -> list[str]:
        """纯向量检索"""
        query_emb = self.embedder.embed([query])[0]
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents"],
        )
        return results["ids"][0] if results["ids"] else []

    def bm25_search(self, query: str, top_k: int) -> list[tuple[str, float]]:
        """BM25 关键词检索"""
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self._ids[i], float(s)) for i, s in ranked if s > 0]

    def hybrid_search(self, query: str, top_k: int) -> list[str]:
        """混合检索 (Vector + BM25 + RRF)"""
        fetch_k = top_k * VECTOR_CANDIDATE_MULTIPLIER

        # 向量
        vec_ids = self.vector_search(query, fetch_k)
        # BM25
        bm25_hits = self.bm25_search(query, fetch_k)

        # RRF 融合
        rrf_scores: dict[str, float] = {}
        for rank, vid in enumerate(vec_ids):
            rrf_scores[vid] = rrf_scores.get(vid, 0) + 1.0 / (RRF_K + rank + 1)
        for rank, (did, _) in enumerate(bm25_hits):
            rrf_scores[did] = rrf_scores.get(did, 0) + 1.0 / (RRF_K + rank + 1)

        return sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]


def _evaluate(dataset: list[dict], search_fn) -> dict[str, float]:
    recall_3 = recall_5 = mrr_sum = hit_5 = 0.0
    n = len(dataset)

    for item in dataset:
        retrieved = search_fn(item["query"], TOP_K)
        relevant = item["relevant_ids"]
        recall_3 += recall_at_k(retrieved, relevant, 3)
        recall_5 += recall_at_k(retrieved, relevant, 5)
        mrr_sum += mrr(retrieved, relevant)
        hit_5 += hit_rate(retrieved, relevant, 5)

    return {
        "Recall@3": recall_3 / n,
        "Recall@5": recall_5 / n,
        "MRR": mrr_sum / n,
        "Hit Rate@5": hit_5 / n,
    }


def main() -> None:
    if not DATASET_PATH.exists():
        print("数据集不存在，请先运行: uv run python -m tests.generate_eval_dataset")
        return

    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    print(f"加载评测数据集: {len(dataset)} 条")

    retriever = EvalRetriever()

    print("正在运行纯向量检索评测...")
    vector_metrics = _evaluate(dataset, retriever.vector_search)

    print("正在运行混合检索评测...")
    hybrid_metrics = _evaluate(dataset, retriever.hybrid_search)

    # 输出报告
    print("\n" + "=" * 55)
    print(f"  检索评测报告 | 数据集: {len(dataset)} 条 | Top-K: {TOP_K}")
    print("=" * 55)
    print(f"  {'指标':<14} {'纯向量':>10} {'混合检索':>10} {'提升':>10}")
    print("-" * 55)

    for key in vector_metrics:
        v = vector_metrics[key]
        h = hybrid_metrics[key]
        diff = h - v
        sign = "+" if diff >= 0 else ""
        print(f"  {key:<14} {fmt(v):>10} {fmt(h):>10} {sign}{diff:.2%}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
