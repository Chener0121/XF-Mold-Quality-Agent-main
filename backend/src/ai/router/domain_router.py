"""Domain Router — rule-based + retrieval-based 查询领域路由，不使用 LLM"""

from src.ai.rag.retrievers.retriever import Retriever
from src.core.logger import get_logger

logger = get_logger(__name__)

# ── Layer 1: 关键词规则（统一小写） ──

_RD_KEYWORDS = {
    "dfmea", "ap", "七步法", "失效", "参数图", "结构树",
    "结构分析", "功能分析", "失效分析", "设计fmea",
    "模具设计", "工艺开发", "研发", "rd",
}

_QUALITY_KEYWORDS = {
    "审核", "capa", "不合格品", "质量方针", "供应商",
    "过程控制", "检验", "vda", "iso",
    "管理评审", "内部审核", "顾客满意", "纠正措施", "预防措施",
    "质量目标", "质量手册", "乌龟图",
}

_SHARED_KEYWORDS = {"fmea", "控制计划", "特殊特性"}


def _keyword_route(query: str) -> str | None:
    """关键词匹配，返回 domain 或 None（未命中）。统一小写比较。"""
    q = query.lower()

    rd_hit = any(kw in q for kw in _RD_KEYWORDS)
    quality_hit = any(kw in q for kw in _QUALITY_KEYWORDS)
    shared_hit = any(kw in q for kw in _SHARED_KEYWORDS)

    if rd_hit and quality_hit:
        return "general"
    if shared_hit and not rd_hit and not quality_hit:
        return "general"
    if rd_hit:
        return "rd"
    if quality_hit:
        return "quality"

    return None


# ── Layer 2: Retrieval-based fallback ──

_retriever: Retriever | None = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _retrieval_route(query: str) -> str:
    """基于检索结果的 score 加权投票判断领域"""
    retriever = _get_retriever()
    hits = retriever.retrieve(query, top_k=3)

    if not hits:
        return "general"

    domain_weights: dict[str, float] = {}
    for hit in hits:
        domain = hit.metadata.get("primary_domain", "general")
        domain_weights[domain] = domain_weights.get(domain, 0) + hit.score

    total_weight = sum(domain_weights.values())
    if not total_weight:
        return "general"

    best = max(domain_weights, key=domain_weights.get)
    if domain_weights[best] / total_weight > 0.5:
        return best

    return "general"


async def route_domain(query: str) -> str:
    """
    路由查询到对应领域。
    Layer 1: 关键词匹配（零延迟）
    Layer 2: retrieval-based score 加权投票（一次向量检索）
    返回: "quality" | "rd" | "general"
    """
    domain = _keyword_route(query)
    if domain:
        logger.info("Domain routed by keyword: %s → %s", query[:30], domain)
        return domain

    domain = _retrieval_route(query)
    logger.info("Domain routed by retrieval: %s → %s", query[:30], domain)
    return domain
