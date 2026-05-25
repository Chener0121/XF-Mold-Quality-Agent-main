"""语义处理器 — 将 RawDocumentElement 转换为 SemanticBlock，支持标题层级传播和领域分类"""

import re

from src.ai.rag.retrievers.domain_classifier import classify_domain
from src.core.logger import get_logger
from src.document.parsers.docx_parser import ElementType, RawDocumentElement
from src.document.processors.semantic_block import SemanticBlock

logger = get_logger(__name__)

_STOP_WORDS: set[str] = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "他", "她", "它", "们", "那", "被", "从", "把", "对", "让", "与",
    "及", "等", "为", "中", "或", "其", "可", "以", "将", "所", "由", "于", "而",
}

# 从 style name 提取标题层级："Heading 1" → 0, "Heading 2" → 1, ...
_HEADING_RE = re.compile(r"Heading\s+(\d+)")


def _heading_level(style: str) -> int | None:
    m = _HEADING_RE.match(style)
    if m:
        return int(m.group(1)) - 1
    return None


def _extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    segments = re.split(r"[，。！？；：、\s,.!?;:\-—·]+", text)
    freq: dict[str, int] = {}
    for seg in segments:
        seg = seg.strip()
        if len(seg) < 2 or seg in _STOP_WORDS:
            continue
        freq[seg] = freq.get(seg, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:max_keywords]]


def _table_summary(markdown_text: str, metadata: dict) -> str:
    lines = markdown_text.strip().split("\n")
    if len(lines) < 2:
        return ""
    headers = [h.strip() for h in lines[0].strip("|").split("|")]
    row_count = metadata.get("row_count", len(lines) - 2)
    col_count = metadata.get("col_count", len(headers))
    return f"表格: {row_count}行×{col_count}列, 列: [{', '.join(headers)}]"


class HeadingStack:
    def __init__(self):
        self._stack: list[str] = []

    def push(self, level: int, title: str) -> None:
        self._stack = self._stack[:level]
        self._stack.append(title.strip())

    def get_path(self) -> list[str]:
        return list(self._stack)

    def get_context_text(self) -> str:
        return " > ".join(self._stack) if self._stack else ""


SHORT_BLOCK_THRESHOLD = 150  # ≤150 字符视为短块
MERGE_MAX_LENGTH = 1000      # 合并后最大长度


class SemanticProcessor:
    """RawDocumentElement → SemanticBlock，标题层级传播"""

    def process(self, elements: list[RawDocumentElement], source: str = "") -> list[SemanticBlock]:
        blocks: list[SemanticBlock] = []
        heading_stack = HeadingStack()

        for elem in elements:
            match elem.type:
                case ElementType.PARAGRAPH:
                    self._process_paragraph(elem, source, heading_stack, blocks)
                case ElementType.TABLE:
                    self._process_table(elem, source, heading_stack, blocks)
                case ElementType.IMAGE:
                    self._process_image(elem, source, heading_stack, blocks)

        merged = self._merge_short_blocks(blocks)
        # 领域分类
        for block in merged:
            domain_info = classify_domain(
                heading_path=block.metadata.get("heading_path", []),
                content=block.content,
                source=block.source,
            )
            block.metadata["domains"] = domain_info["domains"]
            block.metadata["primary_domain"] = domain_info["primary_domain"]

        logger.info("语义转换完成: %d 个元素 → %d 个语义块 (合并前 %d)", len(elements), len(merged), len(blocks))
        return merged

    def _merge_short_blocks(self, blocks: list[SemanticBlock]) -> list[SemanticBlock]:
        """合并连续的非标题短块，保持语义完整"""
        result: list[SemanticBlock] = []
        i = 0

        while i < len(blocks):
            block = blocks[i]

            # 标题、表格、图片不合并
            if block.metadata.get("is_heading") or block.type != "text":
                result.append(block)
                i += 1
                continue

            # 去掉前缀后的纯文本长度
            plain = self._strip_heading_prefix(block.content)

            if len(plain) <= SHORT_BLOCK_THRESHOLD:
                # 开始收集连续短块
                group: list[SemanticBlock] = [block]
                j = i + 1
                total_len = len(plain)

                while j < len(blocks):
                    next_block = blocks[j]
                    if next_block.metadata.get("is_heading"):
                        break
                    if next_block.type != "text":
                        break
                    next_plain = self._strip_heading_prefix(next_block.content)
                    if len(next_plain) > SHORT_BLOCK_THRESHOLD:
                        break
                    if total_len + len(next_plain) + 1 > MERGE_MAX_LENGTH:
                        break
                    group.append(next_block)
                    total_len += len(next_plain) + 1
                    j += 1

                if len(group) > 1:
                    result.append(self._combine_blocks(group))
                    i = j
                else:
                    result.append(block)
                    i += 1
            else:
                result.append(block)
                i += 1

        return result

    @staticmethod
    def _strip_heading_prefix(text: str) -> str:
        """去掉 [xxx > yyy] 前缀，返回纯文本"""
        if text.startswith("["):
            nl = text.find("]\n")
            if nl != -1:
                return text[nl + 2:]
        return text

    @staticmethod
    def _combine_blocks(group: list[SemanticBlock]) -> SemanticBlock:
        """将多个短块合并为一个"""
        first = group[0]
        context_prefix = ""
        if first.content.startswith("["):
            nl = first.content.find("]\n")
            if nl != -1:
                context_prefix = first.content[: nl + 2]

        parts = []
        for b in group:
            plain = SemanticProcessor._strip_heading_prefix(b.content)
            parts.append(plain)

        combined_text = context_prefix + "\n".join(parts)
        combined_keywords = list({kw for b in group for kw in b.keywords})

        return SemanticBlock(
            type="text",
            content=combined_text,
            summary=combined_text[:200] + ("..." if len(combined_text) > 200 else ""),
            keywords=combined_keywords[:10],
            source=first.source,
            index=first.index,
            page=first.page,
            metadata={
                **first.metadata,
                "merged_count": len(group),
            },
        )

    def _process_paragraph(self, elem: RawDocumentElement, source: str,
                           hs: HeadingStack, blocks: list[SemanticBlock]) -> None:
        text = elem.content.strip()
        if not text:
            return

        style = elem.metadata.get("style", "")
        level = _heading_level(style)

        if level is not None:
            # 标题段落 → 更新层级栈
            hs.push(level, text)
            blocks.append(SemanticBlock(
                type="text",
                content=text,
                summary=text,
                keywords=_extract_keywords(text),
                source=source,
                index=elem.index,
                page=elem.page,
                metadata={
                    **elem.metadata,
                    "is_heading": True,
                    "heading_level": level,
                    "heading_path": hs.get_path(),
                },
            ))
            return

        # 正文 — prepend 标题上下文
        context = hs.get_context_text()
        enriched = f"[{context}]\n{text}" if context else text
        summary = text[:200] + ("..." if len(text) > 200 else "")

        blocks.append(SemanticBlock(
            type="text",
            content=enriched,
            summary=summary,
            keywords=_extract_keywords(text),
            source=source,
            index=elem.index,
            page=elem.page,
            metadata={
                **elem.metadata,
                "heading_path": hs.get_path(),
                "section_title": hs.get_path()[-1] if hs.get_path() else "",
            },
        ))

    def _process_table(self, elem: RawDocumentElement, source: str,
                       hs: HeadingStack, blocks: list[SemanticBlock]) -> None:
        md = elem.content
        if not md.strip():
            return

        context = hs.get_context_text()
        enriched = f"[{context}]\n{md}" if context else md

        blocks.append(SemanticBlock(
            type="table",
            content=enriched,
            summary=_table_summary(md, elem.metadata),
            keywords=_extract_keywords(md),
            source=source,
            index=elem.index,
            page=elem.page,
            metadata={
                **elem.metadata,
                "heading_path": hs.get_path(),
                "section_title": hs.get_path()[-1] if hs.get_path() else "",
            },
        ))

    def _process_image(self, elem: RawDocumentElement, source: str,
                       hs: HeadingStack, blocks: list[SemanticBlock]) -> None:
        meta = {**elem.metadata}
        if elem.image_ref:
            meta["image_ref"] = elem.image_ref
        meta["heading_path"] = hs.get_path()
        if hs.get_path():
            meta["section_title"] = hs.get_path()[-1]

        blocks.append(SemanticBlock(
            type="image",
            content="",
            summary="",
            keywords=[],
            source=source,
            index=elem.index,
            page=elem.page,
            metadata=meta,
        ))
