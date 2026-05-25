"""RAG 检索日志 — JSON 持久化到 logs/rag/"""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.ai.rag.evaluation.retrieval_trace import RetrievalTrace
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class RetrievalLogger:
    def __init__(self, log_dir: str | Path | None = None):
        self.log_dir = Path(log_dir) if log_dir else Path("logs/rag")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, trace: RetrievalTrace) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{hash(trace.query) % 10000:04d}.json"
        path = self.log_dir / filename
        path.write_text(trace.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("RAG trace 已保存: %s", path.name)
