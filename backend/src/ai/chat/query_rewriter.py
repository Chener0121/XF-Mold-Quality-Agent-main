"""Query Rewriter — 基于对话历史将上下文依赖型 query 改写为独立完整问题"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.core.llm_client import get_chat_llm

_REWRITE_SYSTEM = """\
你是一个查询改写助手。根据对话历史，将用户的最新问题改写为一个独立的、信息完整的问题。

规则：
1. 补全代词和省略（如"它"→具体名称，"怎么算"→完整问题）
2. 结合历史上下文补充必要的领域信息
3. 如果问题已经是完整的，直接返回原问题
4. 只返回改写后的问题，不要解释"""

_REWRITE_TEMPLATE = """\
对话历史：
{history}

用户最新问题：{query}

改写后的独立问题："""


async def rewrite_query(query: str, history: list[dict]) -> str:
    """
    基于对话历史改写 query。
    history 格式: [{"role": "user"/"assistant", "content": "..."}]
    """
    if not history:
        return query

    history_text = "\n".join(
        f"{'用户' if h['role'] == 'user' else '助手'}：{h['content']}"
        for h in history
    )

    llm = get_chat_llm()
    response = await llm.ainvoke([
        SystemMessage(content=_REWRITE_SYSTEM),
        HumanMessage(content=_REWRITE_TEMPLATE.format(
            history=history_text, query=query,
        )),
    ])

    return response.content.strip() or query
