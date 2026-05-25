from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.core.config import settings


def get_chat_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        model=settings.LLM_MODEL,
        temperature=0,
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        model=settings.LLM_EMBEDDING_MODEL,
    )
