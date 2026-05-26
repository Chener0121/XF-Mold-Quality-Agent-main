"""Rewrite Trigger — 判断 query 是否需要基于历史上下文改写"""

import re

from src.models.entities.conversation import Message

# 指代词 / 追问词 / 省略句式
_PRONOUN_PATTERNS = [
    r'它|这个|那个|这|那|其|他|她',
    r'然后呢|接着|还有呢|继续|接下来',
    r'怎么[算做搞用写看]?$',       # 短句结尾："怎么算？"
    r'呢|吗|的$',
]

_SHORT_QUERY_THRESHOLD = 10  # 字符数


def should_rewrite(query: str, history: list[Message]) -> bool:
    """判断是否需要 rewrite。无 history 时永远不需要。"""
    if not history:
        return False

    stripped = query.strip()

    # 短句 + 有历史 → 默认需要 rewrite
    if len(stripped) <= _SHORT_QUERY_THRESHOLD:
        return True

    # 匹配代词/追问模式
    for pattern in _PRONOUN_PATTERNS:
        if re.search(pattern, stripped):
            return True

    return False
