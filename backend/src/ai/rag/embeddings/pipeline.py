"""Embedding Pipeline — SemanticBlock → EmbeddedBlock

与 FastAPI / parser / VLM 解耦，纯 Python pipeline。
"""

import uuid

from src.core.logger import get_logger
from src.ai.rag.embeddings.embedder import Embedder
from src.ai.rag.embeddings.models import EmbeddedBlock
from src.document.processors.semantic_block import SemanticBlock

logger = get_logger(__name__)


def _build_embedding_text(block: SemanticBlock) -> str:
    """拼接 embedding 输入文本: summary + content + keywords"""
    parts: list[str] = []

    if block.summary:
        parts.append(block.summary)
    if block.content:
        parts.append(block.content)
    if block.keywords:
        parts.append(" ".join(block.keywords))

    return "\n".join(parts)


class EmbeddingPipeline:
    """SemanticBlock → EmbeddedBlock"""

    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or Embedder()

    def run(self, blocks: list[SemanticBlock]) -> list[EmbeddedBlock]:
        if not blocks:
            return []

        # 跳过 content 为空的块（未经 VLM 处理的 image）
        valid: list[tuple[int, SemanticBlock, str]] = []
        for block in blocks:
            text = _build_embedding_text(block)
            if not text.strip():
                logger.warning("跳过空内容块: index=%d, type=%s", block.index, block.type)
                continue
            valid.append((len(valid), block, text))

        if not valid:
            logger.warning("无可嵌入的内容块")
            return []

        # 批量 embedding
        texts = [t for _, _, t in valid]
        vectors = self.embedder.embed(texts)

        # 组装结果
        results: list[EmbeddedBlock] = []
        for (i, block, text), embedding in zip(valid, vectors):
            meta = {
                "source": block.source,
                "type": block.type,
                "index": block.index,
                "page": block.page,
                "keywords": block.keywords,
            }
            if block.metadata.get("image_ref"):
                meta["image_ref"] = block.metadata["image_ref"]

            results.append(
                EmbeddedBlock(
                    id=str(uuid.uuid4()),
                    content=text,
                    embedding=embedding,
                    metadata=meta,
                )
            )

        logger.info("Embedding 完成: %d 个块向量化", len(results))
        return results
