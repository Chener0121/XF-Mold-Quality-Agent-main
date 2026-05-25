"""Embedding Pipeline — ChunkedBlock → EmbeddedBlock，支持缓存"""

import uuid

from src.ai.rag.cache.embedding_cache import EmbeddingCache
from src.ai.rag.cache.hash_utils import compute_block_hash
from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.embeddings.models import EmbeddedBlock
from src.core.logger import get_logger
from src.document.processors.chunker import ChunkedBlock

logger = get_logger(__name__)


class EmbeddingPipeline:
    """ChunkedBlock → EmbeddedBlock"""

    def __init__(self, embedder: Embedder | None = None, cache: EmbeddingCache | None = None):
        self.embedder = embedder or Embedder()
        self.cache = cache

    def run(self, blocks: list[ChunkedBlock]) -> list[EmbeddedBlock]:
        if not blocks:
            return []

        # 分离缓存命中和未命中的块
        cached_results: list[tuple[int, EmbeddedBlock]] = []
        to_embed: list[tuple[int, ChunkedBlock, str]] = []

        for i, block in enumerate(blocks):
            if not block.content.strip():
                logger.warning("跳过空内容块: parent=%s", block.parent_id)
                continue

            block_hash = compute_block_hash("chunk", block.content, block.metadata)

            # 查缓存
            if self.cache:
                cached_vec = self.cache.get(block_hash, self.embedder.model)
                if cached_vec is not None:
                    logger.info("Embedding 缓存命中: %s", block_hash[:12])
                    cached_results.append((i, EmbeddedBlock(
                        id=str(uuid.uuid4()),
                        content=block.content,
                        embedding=cached_vec,
                        metadata={"parent_id": block.parent_id, **block.metadata},
                    )))
                    continue

            to_embed.append((i, block, block_hash))

        # 对未命中的批量 embedding
        new_results: list[tuple[int, EmbeddedBlock]] = []
        if to_embed:
            texts = [block.content for _, block, _ in to_embed]
            vectors = self.embedder.embed(texts)

            for (idx, block, block_hash), embedding in zip(to_embed, vectors):
                # 写缓存
                if self.cache:
                    self.cache.save(block_hash, self.embedder.model, embedding)

                new_results.append((idx, EmbeddedBlock(
                    id=str(uuid.uuid4()),
                    content=block.content,
                    embedding=embedding,
                    metadata={"parent_id": block.parent_id, **block.metadata},
                )))

        # 按 index 合并
        all_results = sorted(cached_results + new_results, key=lambda x: x[0])
        logger.info(
            "Embedding 完成: %d 个块 (缓存命中 %d, 新计算 %d)",
            len(all_results), len(cached_results), len(new_results),
        )
        return [r for _, r in all_results]
