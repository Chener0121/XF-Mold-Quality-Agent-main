"""上下文构建器 — 将检索结果拼接为 LLM 可用的 context 文本"""

from src.ai.rag.retrievers.models import RetrievalResult
from src.core.logger import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    def build(self, results: list[RetrievalResult]) -> str:
        """拼接检索结果为结构化上下文"""
        if not results:
            return ""

        parts: list[str] = []
        for i, r in enumerate(results, 1):
            source = r.metadata.get("source", "")
            section = r.metadata.get("section_title", "")
            block_type = r.metadata.get("type", "")

            header_parts = [f"[片段 {i}]"]
            if source:
                header_parts.append(f"文档: {source}")
            if section:
                header_parts.append(f"章节: {section}")
            if block_type:
                header_parts.append(f"类型: {block_type}")

            parts.append(" | ".join(header_parts))
            parts.append(r.content)
            parts.append("")  # 空行分隔

        context = "\n".join(parts)
        logger.info("上下文构建完成: %d 个片段, %d 字符", len(results), len(context))
        return context
