"""文件工具"""

import hashlib
from pathlib import Path


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()
