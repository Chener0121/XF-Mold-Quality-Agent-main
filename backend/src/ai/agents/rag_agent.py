"""RAG Agent — 基于 LangGraph create_react_agent 的多领域智能体"""

from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from src.ai.prompts.rag_prompt import (
    GENERAL_AGENT_PROMPT,
    QUALITY_AGENT_PROMPT,
    RD_AGENT_PROMPT,
)
from src.ai.tools.knowledge_search import general_search, quality_search, rd_search
from src.core.llm_client import get_streaming_chat_llm
from src.core.logger import get_logger

logger = get_logger(__name__)

MAX_RECURSION = 7

_agents: dict[str, CompiledStateGraph] = {}

_AGENT_CONFIG = {
    "quality": {"prompt": QUALITY_AGENT_PROMPT, "tools": [quality_search]},
    "rd": {"prompt": RD_AGENT_PROMPT, "tools": [rd_search]},
    "general": {"prompt": GENERAL_AGENT_PROMPT, "tools": [general_search]},
}


def _get_agent(domain: str | None) -> CompiledStateGraph:
    key = domain if domain in _AGENT_CONFIG else "general"
    if key not in _agents:
        cfg = _AGENT_CONFIG[key]
        _agents[key] = create_react_agent(
            model=get_streaming_chat_llm(),
            tools=cfg["tools"],
            prompt=cfg["prompt"],
        )
    return _agents[key]


def _build_messages(query: str, history: list[dict] | None = None) -> list:
    """构建 LLM 消息列表：历史 + 当前 query"""
    messages = []
    if history:
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            else:
                messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=query))
    return messages


async def ask_stream(
    query: str, domain: str | None = None, history: list[dict] | None = None,
) -> AsyncGenerator[str | dict, None]:
    """
    流式调用 RAG Agent。
    逐 token yield 字符串，流结束后 yield {"__done__": True, "tool_calls": [...]}。
    """
    agent = _get_agent(domain)
    messages = _build_messages(query, history)

    tool_calls: list[dict] = []

    token_count = 0
    event_types: set[str] = set()

    async for event in agent.astream_events(
        {"messages": messages},
        config={"recursion_limit": MAX_RECURSION},
        version="v2",
    ):
        kind = event["event"]
        event_types.add(kind)

        # 收集工具调用结果
        if kind == "on_tool_end":
            output = event["data"].get("output")
            content = ""
            if isinstance(output, str):
                content = output
            elif hasattr(output, "content"):
                content = str(output.content)
            else:
                content = str(output) if output else ""
            tool_calls.append({
                "tool_name": event.get("name", ""),
                "content_preview": content,
            })

        # 流式输出 LLM token
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            token = chunk.content if hasattr(chunk, "content") else ""
            if token:
                token_count += 1
                yield token

    logger.info("ask_stream done: events=%s, tokens=%d, tool_calls=%d", event_types, token_count, len(tool_calls))

    yield {"__done__": True, "tool_calls": tool_calls}
