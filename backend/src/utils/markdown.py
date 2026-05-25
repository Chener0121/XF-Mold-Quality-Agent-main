"""Markdown 处理工具"""

import re


def strip_markdown(text: str) -> str:
    """简单去除 Markdown 格式标记"""
    text = re.sub(r"[#*`_~>|]", "", text)
    return text.strip()
