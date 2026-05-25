"""文档级缓存 — 基于文件 hash 去重"""

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from src.core.logger import get_logger

logger = get_logger(__name__)


class DocumentRecord(BaseModel):
    doc_id: str
    file_hash: str
    filename: str
    created_at: str
    collection_name: str = ""
    block_ids: list[str] = []


class DocumentCache:
    def __init__(self, cache_dir: str | Path):
        self.path = Path(cache_dir) / "documents.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, dict]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, dict]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, file_hash: str) -> DocumentRecord | None:
        data = self._load()
        record = data.get(file_hash)
        if record:
            return DocumentRecord(**record)
        return None

    def save(self, record: DocumentRecord) -> None:
        data = self._load()
        data[record.file_hash] = record.model_dump()
        self._save(data)
        logger.info("文档缓存已保存: %s (hash=%s)", record.filename, record.file_hash[:12])
