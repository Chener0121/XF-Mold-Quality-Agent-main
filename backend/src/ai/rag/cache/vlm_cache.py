"""VLM 结果缓存 — 基于 block hash 避免重复调用"""

import json
from pathlib import Path

from src.core.logger import get_logger

logger = get_logger(__name__)


class VLMCache:
    def __init__(self, cache_dir: str | Path):
        self.dir = Path(cache_dir) / "vlm"
        self.dir.mkdir(parents=True, exist_ok=True)

    def get(self, block_hash: str, model_name: str) -> dict | None:
        path = self.dir / f"{block_hash}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        # 模型不匹配视为失效
        if data.get("model_name") != model_name:
            logger.info("VLM 缓存模型不匹配，跳过: %s", block_hash[:12])
            return None
        return data.get("result")

    def save(self, block_hash: str, model_name: str, result: dict) -> None:
        path = self.dir / f"{block_hash}.json"
        path.write_text(
            json.dumps({"model_name": model_name, "result": result}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("VLM 缓存已保存: %s", block_hash[:12])
