"""Embedding Pipeline — ChunkedBlock → EmbeddedBlock"""

import uuid

from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.embeddings.models import EmbeddedBlock
from src.core.logger import get_logger
from src.document.processors.chunker import ChunkedBlock

logger = get_logger(__name__)


class EmbeddingPipeline:
    """ChunkedBlock → EmbeddedBlock"""

    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or Embedder()

    def run(self, blocks: list[ChunkedBlock]) -> list[EmbeddedBlock]:
        if not blocks:
            return []

        # 过滤空内容
        valid: list[tuple[int, ChunkedBlock]] = []
        for i, block in enumerate(blocks):
            if block.content.strip():
                valid.append((i, block))
            else:
                logger.warning("跳过空内容块: parent=%s", block.parent_id)

        if not valid:
            logger.warning("无可嵌入的内容块")
            return []

        # 批量 embedding
        texts = [block.content for _, block in valid]
        vectors = self.embedder.embed(texts)

        # 组装结果
        results: list[EmbeddedBlock] = []
        for (_, block), embedding in zip(valid, vectors):
            results.append(
                EmbeddedBlock(
                    id=str(uuid.uuid4()),
                    content=block.content,
                    embedding=embedding,
                    metadata={
                        "parent_id": block.parent_id,
                        **block.metadata,
                    },
                )
            )

        logger.info("Embedding 完成: %d 个块向量化", len(results))
        return results
