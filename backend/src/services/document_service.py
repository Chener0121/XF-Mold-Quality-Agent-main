"""文档处理服务 — 串联完整流水线：parser → processor → VLM → embedding → Chroma"""

import shutil
import tempfile
from pathlib import Path

from src.ai.rag.embeddings.pipeline import EmbeddingPipeline
from src.ai.rag.vectorstores.chroma_store import ChromaStore
from src.core.logger import get_logger
from src.document.parsers.docx_parser import DocxParser
from src.document.processors.semantic_processor import SemanticProcessor
from src.document.processors.vlm_processor import VLMProcessor

logger = get_logger(__name__)


class DocumentService:
    def __init__(self, chroma_store: ChromaStore | None = None):
        self.store = chroma_store or ChromaStore()
        self.parser = DocxParser()
        self.semantic_processor = SemanticProcessor()
        self.vlm_processor = VLMProcessor()
        self.embedding_pipeline = EmbeddingPipeline()

    def process_and_store(self, file_path: str | Path, filename: str = "") -> dict:
        """完整处理流水线：解析 → 语义转换 → VLM增强 → embedding → 存储"""
        file_path = Path(file_path)
        source = filename or file_path.name
        logger.info("开始处理文档: %s", source)

        # 1. 解析
        raw_elements = self.parser.parse(file_path)
        logger.info("解析完成: %d 个原始元素", len(raw_elements))

        # 2. 语义转换
        blocks = self.semantic_processor.process(raw_elements, source=source)
        logger.info("语义转换完成: %d 个语义块", len(blocks))

        # 3. VLM 增强
        blocks = self.vlm_processor.enrich_all(blocks)
        logger.info("VLM 增强完成")

        # 4. Embedding
        embedded = self.embedding_pipeline.run(blocks)
        logger.info("Embedding 完成: %d 个向量", len(embedded))

        # 5. 存入 Chroma
        if embedded:
            self.store.add_blocks(embedded)

        return {
            "filename": source,
            "total_elements": len(raw_elements),
            "total_blocks": len(blocks),
            "total_embedded": len(embedded),
            "status": "completed",
        }

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """语义检索"""
        return self.store.similarity_search(query, top_k=top_k)
