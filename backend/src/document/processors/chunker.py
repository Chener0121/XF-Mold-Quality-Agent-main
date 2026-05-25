"""语义切块器 — 将超长 SemanticBlock 拆分为符合 embedding token 限制的 ChunkedBlock

保持业务语义完整性：段落按句子拆分，表格保留表头，图片不拆分。
"""

import re
import uuid
from typing import Any

from pydantic import BaseModel, Field

from src.core.logger import get_logger
from src.document.processors.semantic_block import SemanticBlock

logger = get_logger(__name__)

# 保守估计: 2048 token ≈ ~5000 中文字符
MAX_CHUNK_CHARS = 4000
# 句子间重叠，保持上下文连贯
OVERLAP_CHARS = 200


class ChunkedBlock(BaseModel):
    """切块后的语义子块"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str = ""
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


def _split_sentences(text: str) -> list[str]:
    """按中英文句号、换行等拆分句子"""
    parts = re.split(r"(?<=[。！？\n])", text)
    return [p.strip() for p in parts if p.strip()]


def _chunk_paragraph(block: SemanticBlock) -> list[ChunkedBlock]:
    """段落类型：按句子边界拆分，带重叠"""
    text = block.content
    if len(text) <= MAX_CHUNK_CHARS:
        return [_to_chunked_block(block, text)]

    sentences = _split_sentences(text)
    chunks: list[ChunkedBlock] = []
    current = ""

    for sent in sentences:
        if len(current) + len(sent) > MAX_CHUNK_CHARS and current:
            chunks.append(_to_chunked_block(block, current))
            # 保留尾部重叠
            current = current[-OVERLAP_CHARS:] + "\n" + sent if len(current) > OVERLAP_CHARS else sent
        else:
            current = current + "\n" + sent if current else sent

    if current.strip():
        chunks.append(_to_chunked_block(block, current))

    return chunks if chunks else [_to_chunked_block(block, text)]


def _chunk_table(block: SemanticBlock) -> list[ChunkedBlock]:
    """表格类型：按行拆分，每个 chunk 保留表头"""
    text = block.content
    if len(text) <= MAX_CHUNK_CHARS:
        return [_to_chunked_block(block, text)]

    lines = text.strip().split("\n")
    if len(lines) < 3:
        return [_to_chunked_block(block, text)]

    # 第一行是表头，第二行是分隔线
    header = lines[0]
    separator = lines[1]
    data_rows = lines[2:]

    chunks: list[ChunkedBlock] = []
    current_rows: list[str] = []
    # 表头 + 分隔线的基础长度
    base_len = len(header) + len(separator) + 2

    for row in data_rows:
        if base_len + sum(len(r) for r in current_rows) + len(row) > MAX_CHUNK_CHARS and current_rows:
            chunk_text = "\n".join([header, separator, *current_rows])
            chunks.append(_to_chunked_block(block, chunk_text))
            current_rows = [row]
        else:
            current_rows.append(row)

    if current_rows:
        chunk_text = "\n".join([header, separator, *current_rows])
        chunks.append(_to_chunked_block(block, chunk_text))

    return chunks if chunks else [_to_chunked_block(block, text)]


def _chunk_image(block: SemanticBlock) -> list[ChunkedBlock]:
    """图片类型：通常不切块"""
    return [_to_chunked_block(block, block.content)]


def _to_chunked_block(block: SemanticBlock, content: str) -> ChunkedBlock:
    """构建 ChunkedBlock，继承父块 metadata"""
    meta: dict[str, Any] = {
        "source": block.source,
        "type": block.type,
        "page": block.page,
        "index": block.index,
        "keywords": block.keywords,
    }
    if block.metadata.get("image_ref"):
        meta["image_ref"] = block.metadata["image_ref"]
    if block.metadata.get("image_type"):
        meta["image_type"] = block.metadata["image_type"]

    return ChunkedBlock(
        parent_id=f"{block.source}:{block.index}",
        content=content,
        metadata=meta,
    )


class Chunker:
    """SemanticBlock → ChunkedBlock，语义感知切块"""

    def chunk(self, blocks: list[SemanticBlock]) -> list[ChunkedBlock]:
        result: list[ChunkedBlock] = []
        for block in blocks:
            match block.type:
                case "text":
                    result.extend(_chunk_paragraph(block))
                case "table":
                    result.extend(_chunk_table(block))
                case "image" | _:
                    result.extend(_chunk_image(block))

        logger.info("语义切块完成: %d 个 SemanticBlock → %d 个 ChunkedBlock", len(blocks), len(result))
        return result
