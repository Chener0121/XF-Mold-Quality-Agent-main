"""缓存公共工具 — block hash 计算"""

import hashlib
import json


def compute_block_hash(block_type: str, content: str, metadata: dict) -> str:
    """基于 type + content + metadata 生成稳定 hash"""
    hash_input = block_type + content + json.dumps(metadata, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(hash_input.encode()).hexdigest()
