"""RAG Agent — 基于 LangGraph create_react_agent 的多领域智能体"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
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

MAX_RECURSION = 7  # 3 次搜索 × 2 步 + 最终回答

_agents: dict[str, object] = {}

_AGENT_CONFIG = {
    "quality": {"prompt": QUALITY_AGENT_PROMPT, "tools": [quality_search]},
    "rd": {"prompt": RD_AGENT_PROMPT, "tools": [rd_search]},
    "general": {"prompt": GENERAL_AGENT_PROMPT, "tools": [general_search]},
}


def _get_agent(domain: str | None) -> object:
    key = domain if domain in _AGENT_CONFIG else "general"
    if key not in _agents:
        cfg = _AGENT_CONFIG[key]
        _agents[key] = create_react_agent(
            model=get_chat_llm(),
            tools=cfg["tools"],
            prompt=cfg["prompt"],
        )
    return _agents[key]


def ask(query: str, domain: str | None = None, history: list[dict] | None = None) -> dict:
    """调用对应领域的 RAG Agent 并返回结果"""
    agent = _get_agent(domain)

    # 构建消息列表：历史 + 当前 query
    messages = []
    if history:
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            else:
                messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=query))

    result = agent.invoke(
        {"messages": messages},
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
                "content_preview": msg.content or "",
            })

    logger.info("Agent 完成: domain=%s, messages=%d, tool_calls=%d", domain, len(messages), len(tool_calls))

    return {
        "answer": answer,
        "tool_calls": tool_calls,
    }
