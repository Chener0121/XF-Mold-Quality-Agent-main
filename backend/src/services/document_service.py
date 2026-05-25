"""文档处理服务 — 串联完整流水线，支持缓存去重"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.ai.rag.cache.document_cache import DocumentCache, DocumentRecord
from src.ai.rag.cache.embedding_cache import EmbeddingCache
from src.ai.rag.cache.vlm_cache import VLMCache
from src.ai.rag.embeddings.pipeline import EmbeddingPipeline
from src.ai.rag.vectorstores.chroma_store import ChromaStore
from src.core.config import settings
from src.core.logger import get_logger
from src.utils.file import file_hash
from src.document.parsers.docx_parser import DocxParser
from src.document.processors.chunker import Chunker
from src.document.processors.semantic_processor import SemanticProcessor
from src.document.processors.vlm_processor import VLMProcessor

logger = get_logger(__name__)


class DocumentService:
    def __init__(self, chroma_store: ChromaStore | None = None):
        self.store = chroma_store or ChromaStore()
        self.doc_cache = DocumentCache(settings.CACHE_DIR)
        self.vlm_cache = VLMCache(settings.CACHE_DIR)
        self.embedding_cache = EmbeddingCache(settings.CACHE_DIR)

        self.parser = DocxParser()
        self.semantic_processor = SemanticProcessor()
        self.vlm_processor = VLMProcessor(vlm_cache=self.vlm_cache)
        self.chunker = Chunker()
        self.embedding_pipeline = EmbeddingPipeline(cache=self.embedding_cache)

    def process_and_store(
        self,
        file_path: str | Path,
        filename: str = "",
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict:
        file_path = Path(file_path)
        source = filename or file_path.name
        logger.info("开始处理文档: %s", source)

        def progress(stage: str, **kwargs):
            logger.info("[%s] %s", stage, kwargs)
            if on_progress:
                on_progress(stage, {"filename": source, **kwargs})

        # 0. 文档级去重
        file_hash = file_hash(file_path)
        existing = self.doc_cache.get(file_hash)
        if existing:
            logger.info("文档已存在，跳过处理: %s (doc_id=%s)", source, existing.doc_id)
            return {
                "filename": source,
                "status": "skipped (already processed)",
                "doc_id": existing.doc_id,
                "total_embedded": len(existing.block_ids),
            }

        progress("parsing")
        raw_elements = self.parser.parse(file_path)
        progress("parsed", total_elements=len(raw_elements))

        progress("processing")
        blocks = self.semantic_processor.process(raw_elements, source=source)
        progress("processed", total_blocks=len(blocks))

        progress("enriching")
        blocks = self.vlm_processor.enrich_all(blocks)
        image_count = sum(1 for b in blocks if b.type == "image")
        progress("enriched", images_enriched=image_count)

        progress("chunking")
        chunked = self.chunker.chunk(blocks)
        progress("chunked", total_chunks=len(chunked))

        progress("embedding")
        embedded = self.embedding_pipeline.run(chunked)
        progress("embedded", total_embedded=len(embedded))

        block_ids: list[str] = []
        if embedded:
            self.store.add_blocks(embedded)
            block_ids = [e.id for e in embedded]

        # 记录文档缓存
        doc_id = f"{hash(file_hash + source) & 0xFFFFFFFF:08x}"
        self.doc_cache.save(DocumentRecord(
            doc_id=doc_id,
            file_hash=file_hash,
            filename=source,
            created_at=datetime.now(timezone.utc).isoformat(),
            collection_name="semantic_blocks",
            block_ids=block_ids,
        ))

        progress("completed", total_embedded=len(embedded))
        return {
            "filename": source,
            "total_elements": len(raw_elements),
            "total_blocks": len(blocks),
            "total_embedded": len(embedded),
            "doc_id": doc_id,
            "status": "completed",
        }

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return self.store.similarity_search(query, top_k=top_k)
