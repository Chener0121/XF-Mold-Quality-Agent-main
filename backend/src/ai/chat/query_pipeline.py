"""Query Pipeline — 编排 rewrite → route → retrieve 的完整流程"""

from pydantic import BaseModel

from src.ai.agents.rag_agent import ask as agent_ask
from src.ai.chat.history_manager import build_history_context
from src.ai.chat.rewrite_trigger import should_rewrite
from src.ai.chat.query_rewriter import rewrite_query
from src.ai.router.domain_router import route_domain
from src.models.entities.conversation import Message
from src.core.logger import get_logger

logger = get_logger(__name__)


class PipelineResult(BaseModel):
    rewritten_query: str
    domain: str
    answer: str
    tool_calls: list[dict]


async def process(query: str, history: list[Message]) -> PipelineResult:
    """
    完整的 query 处理 pipeline:
    1. token-aware history truncation
    2. rewrite trigger → query rewrite (if needed)
    3. domain routing
    4. agent retrieval + answer generation
    """
    # 1. 构建 token-aware history context
    history_ctx = build_history_context(history)

    # 2. 判断是否需要 rewrite
    if should_rewrite(query, history):
        rewritten = await rewrite_query(query, history_ctx)
        logger.info("Query rewritten: %r → %r", query, rewritten)
    else:
        rewritten = query

    # 3. 领域路由
    domain = await route_domain(rewritten)

    # 4. Agent retrieval + answer (传入 history)
    result = agent_ask(query=rewritten, domain=domain, history=history_ctx)

    return PipelineResult(
        rewritten_query=rewritten,
        domain=domain,
        answer=result["answer"],
        tool_calls=result.get("tool_calls", []),
    )
