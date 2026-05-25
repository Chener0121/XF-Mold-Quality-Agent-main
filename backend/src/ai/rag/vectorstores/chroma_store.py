"""Chroma 向量存储 — 持久化 EmbeddedBlock 并支持相似度检索"""

from pathlib import Path

import chromadb

from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.embeddings.models import EmbeddedBlock
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class ChromaStore:
    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "semantic_blocks",
    ):
        self.persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = Embedder()
        logger.info("Chroma 初始化: dir=%s, collection=%s", self.persist_dir, collection_name)

    def add_blocks(self, blocks: list[EmbeddedBlock]) -> None:
        """批量插入 EmbeddedBlock"""
        if not blocks:
            return

        ids = [b.id for b in blocks]
        documents = [b.content for b in blocks]
        embeddings = [b.embedding for b in blocks]
        metadatas = []
        for b in blocks:
            meta = {}
            for key in ("source", "type", "index", "page", "image_ref", "keywords"):
                if key in b.metadata and b.metadata[key] is not None:
                    val = b.metadata[key]
                    # Chroma metadata 值必须是 str/int/float/bool
                    if isinstance(val, list):
                        val = ", ".join(str(v) for v in val)
                    meta[key] = val
            metadatas.append(meta)

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Chroma 插入: %d 个块", len(blocks))

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """基于查询文本进行相似度检索"""
        query_embedding = self.embedder.embed([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        for i, doc_id in enumerate(results["ids"][0]):
            hits.append({
                "id": doc_id,
                "content": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
        return hits
