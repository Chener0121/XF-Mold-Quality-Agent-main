"""Query Pipeline — 编排 rewrite → agent streaming 的完整流程"""

from collections.abc import AsyncGenerator

from src.ai.agents.rag_agent import ask_stream as agent_ask_stream
from src.ai.chat.history_manager import build_history_context
from src.ai.chat.rewrite_trigger import should_rewrite
from src.ai.chat.query_rewriter import rewrite_query
from src.models.entities.conversation import Message
from src.core.logger import get_logger

logger = get_logger(__name__)


async def process_stream(
    query: str,
    history: list[Message],
    agent: str | None = None,
    document_ids: list[str] | None = None,
    rules: str | None = None,
) -> AsyncGenerator[tuple[str, dict], None]:
    """
    流式 query 处理 pipeline:
    1. token-aware history truncation
    2. rewrite trigger → query rewrite (if needed)
    3. agent streaming retrieval + answer generation

    yield ("meta", {...})  — 前置元信息
    yield ("token", {content: str})  — 逐字 token
    yield ("done", {tool_calls: list})  — 流结束 + retrievals
    """
    history_ctx = build_history_context(history)
    if should_rewrite(query, history):
        rewritten = await rewrite_query(query, history_ctx)
        logger.info("Query rewritten: %r → %r", query, rewritten)
    else:
        rewritten = query

    domain = agent if agent else "general"

    yield ("meta", {
        "domain": domain,
        "rewritten_query": rewritten if rewritten != query else None,
    })

    tool_calls: list[dict] = []
    async for item in agent_ask_stream(
        query=rewritten, domain=domain, history=history_ctx,
        document_ids=document_ids, rules=rules,
    ):
        if isinstance(item, dict) and item.get("__done__"):
            tool_calls = item.get("tool_calls", [])
        elif isinstance(item, tuple) and item[0] == "thinking":
            yield ("thinking", {"content": item[1]})
        else:
            yield ("token", {"content": item})

    yield ("done", {"tool_calls": tool_calls})
