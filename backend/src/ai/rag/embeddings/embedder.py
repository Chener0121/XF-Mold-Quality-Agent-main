"""Embedding 客户端 — 封装 OpenAI 兼容的 embedding API"""

from openai import OpenAI

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class Embedder:
    """文本向量化客户端"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_API_BASE
        self.model = model or settings.LLM_EMBEDDING_MODEL
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化"""
        if not texts:
            return []

        logger.info("Embedding: %d 条文本 (model=%s)", len(texts), self.model)
        response = self._client.embeddings.create(
            model=self.model,
            input=texts,
        )
        # 按 index 排序确保顺序一致
        data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in data]
