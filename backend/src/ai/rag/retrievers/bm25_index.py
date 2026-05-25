"""BM25 索引 — 从 ChromaDB 加载全量文档构建关键词检索"""

import jieba
from rank_bm25 import BM25Okapi

from src.ai.rag.vectorstores.chroma_store import ChromaStore
from src.core.logger import get_logger

logger = get_logger(__name__)


def _tokenize(text: str) -> list[str]:
    """中文分词 + 过滤空白"""
    return [w for w in jieba.cut(text) if w.strip()]


class BM25Index:
    """基于 rank_bm25 的关键词检索索引，懒加载自动构建"""

    def __init__(self, store: ChromaStore | None = None):
        self._store = store
        self._bm25: BM25Okapi | None = None
        self._ids: list[str] = []
        self._contents: list[str] = []
        self._metadatas: list[dict] = []
        self._doc_count: int = -1

    def _ensure_loaded(self) -> None:
        store = self._store or ChromaStore()
        current_count = store.collection.count()

        # 数据量变化时重建索引
        if self._bm25 is None or current_count != self._doc_count:
            self._build(store)

    def _build(self, store: ChromaStore) -> None:
        collection = store.collection
        self._doc_count = collection.count()

        if self._doc_count == 0:
            self._bm25 = None
            return

        result = collection.get(include=["documents", "metadatas"])
        self._ids = result["ids"]
        self._contents = result["documents"] or [""] * len(self._ids)
        self._metadatas = result["metadatas"] or [{}] * len(self._ids)

        tokenized_corpus = [_tokenize(doc) for doc in self._contents]
        self._bm25 = BM25Okapi(tokenized_corpus)
        logger.info("BM25 索引构建完成: %d 条文档", self._doc_count)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """返回 [(doc_id, bm25_score), ...]"""
        self._ensure_loaded()
        if self._bm25 is None:
            return []

        tokenized_query = _tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # 按 score 降序取 top_k
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self._ids[i], float(score)) for i, score in ranked if score > 0]

    @property
    def doc_count(self) -> int:
        return self._doc_count
