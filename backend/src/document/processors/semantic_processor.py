"""语义处理器 — 将 RawDocumentElement 转换为 SemanticBlock

与 parser / VLM / FastAPI / pgvector 完全解耦，纯 Python 可测试。
"""

import re

from src.core.logger import get_logger
from src.document.parsers.docx_parser import ElementType, RawDocumentElement
from src.document.processors.semantic_block import SemanticBlock

logger = get_logger(__name__)

# 简单的中文停用词（仅用于 keyword 提取）
_STOP_WORDS: set[str] = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "他", "她", "它", "们", "那", "被", "从", "把", "对", "让", "与",
    "及", "等", "为", "中", "或", "其", "可", "以", "将", "所", "由", "于", "而",
}


def _extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """基于词频的简单关键词提取（无 LLM）"""
    # 按标点和空白分割
    segments = re.split(r"[，。！？；：、\s,.!?;:\-—·]+", text)
    freq: dict[str, int] = {}
    for seg in segments:
        seg = seg.strip()
        if len(seg) < 2 or seg in _STOP_WORDS:
            continue
        freq[seg] = freq.get(seg, 0) + 1
    # 按频率排序，取 top N
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:max_keywords]]


def _table_summary(markdown_text: str, metadata: dict) -> str:
    """从 markdown 表格生成结构化摘要"""
    lines = markdown_text.strip().split("\n")
    if len(lines) < 2:
        return ""

    # 第一行是表头
    headers = [h.strip() for h in lines[0].strip("|").split("|")]
    row_count = metadata.get("row_count", len(lines) - 2)
    col_count = metadata.get("col_count", len(headers))

    return f"表格: {row_count}行×{col_count}列, 列: [{', '.join(headers)}]"


class SemanticProcessor:
    """RawDocumentElement → SemanticBlock"""

    def process(self, elements: list[RawDocumentElement], source: str = "") -> list[SemanticBlock]:
        blocks: list[SemanticBlock] = []
        for elem in elements:
            block = self._convert(elem, source)
            blocks.append(block)
        logger.info("语义转换完成: %d 个元素 → %d 个语义块", len(elements), len(blocks))
        return blocks

    def _convert(self, elem: RawDocumentElement, source: str) -> SemanticBlock:
        match elem.type:
            case ElementType.PARAGRAPH:
                return self._from_paragraph(elem, source)
            case ElementType.TABLE:
                return self._from_table(elem, source)
            case ElementType.IMAGE:
                return self._from_image(elem, source)

    @staticmethod
    def _from_paragraph(elem: RawDocumentElement, source: str) -> SemanticBlock:
        text = elem.content
        # 摘要: 取前 200 字符
        summary = text[:200] + ("..." if len(text) > 200 else "")
        return SemanticBlock(
            type="text",
            content=text,
            summary=summary,
            keywords=_extract_keywords(text),
            source=source,
            index=elem.index,
            page=elem.page,
            metadata=elem.metadata,
        )

    @staticmethod
    def _from_table(elem: RawDocumentElement, source: str) -> SemanticBlock:
        md = elem.content
        summary = _table_summary(md, elem.metadata)
        return SemanticBlock(
            type="table",
            content=md,
            summary=summary,
            keywords=_extract_keywords(md),
            source=source,
            index=elem.index,
            page=elem.page,
            metadata=elem.metadata,
        )

    @staticmethod
    def _from_image(elem: RawDocumentElement, source: str) -> SemanticBlock:
        # 当前阶段不调用 VLM，content 留空，保留 image_ref
        meta = {**elem.metadata}
        if elem.image_ref:
            meta["image_ref"] = elem.image_ref
        return SemanticBlock(
            type="image",
            content="",
            summary="",
            keywords=[],
            source=source,
            index=elem.index,
            page=elem.page,
            metadata=meta,
        )
