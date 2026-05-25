"""文档处理服务 — 串联完整流水线：parser → processor → VLM → embedding → Chroma"""

from pathlib import Path
from typing import Any, Callable

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

    def process_and_store(
        self,
        file_path: str | Path,
        filename: str = "",
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict:
        """完整处理流水线，支持进度回调"""
        file_path = Path(file_path)
        source = filename or file_path.name
        logger.info("开始处理文档: %s", source)

        def progress(stage: str, **kwargs):
            logger.info("[%s] %s", stage, kwargs)
            if on_progress:
                on_progress(stage, {"filename": source, **kwargs})

        # 1. 解析
        progress("parsing")
        raw_elements = self.parser.parse(file_path)
        progress("parsed", total_elements=len(raw_elements))

        # 2. 语义转换
        progress("processing")
        blocks = self.semantic_processor.process(raw_elements, source=source)
        progress("processed", total_blocks=len(blocks))

        # 3. VLM 增强
        progress("enriching")
        blocks = self.vlm_processor.enrich_all(blocks)
        image_count = sum(1 for b in blocks if b.type == "image")
        progress("enriched", images_enriched=image_count)

        # 4. Embedding
        progress("embedding")
        embedded = self.embedding_pipeline.run(blocks)
        progress("embedded", total_embedded=len(embedded))

        # 5. 存入 Chroma
        if embedded:
            self.store.add_blocks(embedded)

        progress("completed", total_embedded=len(embedded))
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
