"""RAG Agent — 基于 LangGraph create_react_agent 的多领域智能体"""

from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from src.ai.prompts.rag_prompt import (
    GENERAL_AGENT_PROMPT,
    QUALITY_AGENT_PROMPT,
    RD_AGENT_PROMPT,
)
from src.ai.tools.knowledge_search import general_search, quality_search, rd_search
from src.core.llm_client import get_chat_llm
from src.core.logger import get_logger

logger = get_logger(__name__)

MAX_RECURSION = 6  # 最多 3 轮工具调用（每轮 = AIMessage + ToolMessage）

_agents: dict[str, object] = {}

_AGENT_CONFIG = {
    "quality": {"prompt": QUALITY_AGENT_PROMPT, "tools": [quality_search]},
    "rd": {"prompt": RD_AGENT_PROMPT, "tools": [rd_search]},
    "general": {"prompt": GENERAL_AGENT_PROMPT, "tools": [general_search]},
}


def _get_agent(domain: str | None) -> object:
    key = domain or "general"
    if key not in _agents:
        cfg = _AGENT_CONFIG[key]
        _agents[key] = create_react_agent(
            model=get_chat_llm(),
            tools=cfg["tools"],
            prompt=cfg["prompt"],
        )
    return _agents[key]


def ask(query: str, domain: str | None = None) -> dict:
    """调用对应领域的 RAG Agent 并返回结果"""
    agent = _get_agent(domain)
    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"recursion_limit": MAX_RECURSION},
    )

    messages = result["messages"]

    # 从消息历史中提取最终 AI 回答
    answer = ""
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage) and msg.content:
            answer = msg.content
            break

    # 提取工具调用记录
    tool_calls = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_calls.append({
                "tool_name": msg.name or "",
                "content_preview": msg.content[:500] if msg.content else "",
            })

    logger.info("Agent 完成: domain=%s, messages=%d, tool_calls=%d", domain, len(messages), len(tool_calls))

    return {
        "answer": answer,
        "tool_calls": tool_calls,
    }
