"""Agent 公共工具 — LLM 调用封装"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.ai.prompts.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE
from src.core.llm_client import get_chat_llm


def invoke_llm(context: str, question: str) -> str:
    """调用 LLM 生成 RAG 回答"""
    llm = get_chat_llm()
    response = llm.invoke([
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=RAG_USER_TEMPLATE.format(context=context, question=question)),
    ])
    return response.content if hasattr(response, "content") else str(response)
