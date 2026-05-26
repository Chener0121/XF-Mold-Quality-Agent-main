"""Token-aware history truncation — 从最新消息向前填充，超出时裁剪最早消息"""

import re

from src.models.entities.conversation import Message


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数：中文按字符÷1.5，英文按空格分词"""
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    remaining = len(text) - chinese_chars
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return int(chinese_chars / 1.5) + english_words + remaining // 4


def build_history_context(
    messages: list[Message],
    max_tokens: int = 4000,
) -> list[dict]:
    """
    从最新消息向前填充 history context，直到超出 max_tokens。
    返回 [{"role": "user"/"assistant", "content": "..."}]
    """
    if not messages:
        return []

    result: list[dict] = []
    token_sum = 0

    for msg in reversed(messages):
        tokens = _estimate_tokens(msg.content)
        if token_sum + tokens > max_tokens:
            break
        result.append({"role": msg.role, "content": msg.content})
        token_sum += tokens

    result.reverse()
    return result
