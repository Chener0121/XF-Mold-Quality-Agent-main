"""Embedding 向量缓存 — 基于 block hash 避免重复调用"""

import pickle
from pathlib import Path

from src.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingCache:
    def __init__(self, cache_dir: str | Path):
        self.dir = Path(cache_dir) / "embeddings"
        self.dir.mkdir(parents=True, exist_ok=True)

    def get(self, block_hash: str, model_name: str) -> list[float] | None:
        path = self.dir / f"{block_hash}.pkl"
        if not path.exists():
            return None
        with open(path, "rb") as f:
            data = pickle.load(f)
        # 模型不匹配视为失效
        if data.get("model_name") != model_name:
            logger.info("Embedding 缓存模型不匹配，跳过: %s", block_hash[:12])
            return None
        return data.get("embedding")

    def save(self, block_hash: str, model_name: str, embedding: list[float]) -> None:
        path = self.dir / f"{block_hash}.pkl"
        with open(path, "wb") as f:
            pickle.dump({"model_name": model_name, "embedding": embedding}, f)
        logger.info("Embedding 缓存已保存: %s", block_hash[:12])
