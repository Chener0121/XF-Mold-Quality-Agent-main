"""领域分类器 — 根据章节标题/内容判断所属领域"""

import re


# 章节编号 → 领域映射规则
_QUALITY_ONLY_PATTERNS = [
    r"^M(?!7)\d+",          # M1-M6, M8-M9（排除 M7）
    r"^S\d+",               # S 系列
    r"^C[4689](?:\.\d+)*",  # C4, C6, C8, C9
]

_RD_ONLY_PATTERNS = [
    r"^C[23](?:\.\d+)*",    # C2, C3
    r"DFMEA",
]

_SHARED_PATTERNS = [
    (r"^M7", "quality", "rd"),              # M7 项目管理
    (r"C4.*特殊特性", "quality", "rd"),       # 特殊特性
    (r"PFMEA", "quality", "rd"),
    (r"FMEA-MSR", "quality", "rd"),
    (r"七步法", "quality", "rd"),
    (r"严重度|频度|探测度|评级表", "quality", "rd"),
    (r"AP表|行动优先级", "quality", "rd"),
    (r"控制计划", "quality", "rd"),
]

# 质量专属关键词
_QUALITY_KEYWORDS = [
    "质量方针", "质量目标", "ISO", "CAPA", "纠正措施", "预防措施",
    "检验", "审核", "管理评审", "内部审核", "不合格", "顾客满意",
]


def classify_domain(heading_path: list[str], content: str, source: str = "") -> dict:
    """
    根据标题路径、内容和来源文件判断领域。

    返回: {"domains": [...], "primary_domain": "..."}
    """
    path_text = " > ".join(heading_path) if heading_path else ""
    full_text = f"{path_text} {content} {source}"

    # 1. 检查共享模式（优先匹配）
    for pattern, *domains in _SHARED_PATTERNS:
        if re.search(pattern, full_text):
            return {
                "domains": list(domains),
                "primary_domain": domains[0],
            }

    # 2. DFMEA → rd
    if "DFMEA" in full_text:
        return {"domains": ["rd"], "primary_domain": "rd"}

    # 3. 质量专属关键词
    for kw in _QUALITY_KEYWORDS:
        if kw in full_text:
            return {"domains": ["quality"], "primary_domain": "quality"}

    # 4. 编号规则匹配
    # 检查标题路径中每个段落的编号
    for segment in heading_path:
        segment = segment.strip()

        # RD 专属
        for p in _RD_ONLY_PATTERNS:
            if re.search(p, segment):
                return {"domains": ["rd"], "primary_domain": "rd"}

        # Quality 专属
        for p in _QUALITY_ONLY_PATTERNS:
            if re.search(p, segment):
                return {"domains": ["quality"], "primary_domain": "quality"}

    # 5. 根据文件名判断默认领域
    source_lower = source.lower()
    if "fmea" in source_lower and "pfmea" not in source_lower:
        return {"domains": ["rd"], "primary_domain": "rd"}
    if "vda" in source_lower or "质量" in source_lower or "qms" in source_lower:
        return {"domains": ["quality"], "primary_domain": "quality"}

    # 6. 默认归属两个领域
    return {"domains": ["quality", "rd"], "primary_domain": "quality"}
