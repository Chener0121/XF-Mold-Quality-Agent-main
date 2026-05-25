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

    BATCH_SIZE = 25

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化，自动分批"""
        if not texts:
            return []

        logger.info("Embedding: %d 条文本 (model=%s, batch=%d)", len(texts), self.model, self.BATCH_SIZE)

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i : i + self.BATCH_SIZE]
            logger.info("Embedding 批次 %d/%d (%d 条)", i // self.BATCH_SIZE + 1, -(-len(texts) // self.BATCH_SIZE), len(batch))
            response = self._client.embeddings.create(
                model=self.model,
                input=batch,
            )
            data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend(item.embedding for item in data)

        return all_embeddings
