"""VLM 客户端 — 封装 OpenAI 兼容的多模态调用"""

import base64
from pathlib import Path

from openai import OpenAI

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


def _encode_image(image_path: str) -> str:
    """将图片编码为 base64 data URI"""
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    mime = mime_map.get(suffix, "image/png")
    data = path.read_bytes()
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


class VLMClient:
    """VLM 调用客户端，支持替换不同模型"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_API_BASE
        self.model = model or settings.LLM_VLM_MODEL
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze(self, image_path: str, prompt: str) -> str:
        """调用 VLM 分析图片，返回文本结果"""
        data_uri = _encode_image(image_path)

        logger.info("VLM 分析: %s (model=%s)", image_path, self.model)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            temperature=0,
        )
        result = response.choices[0].message.content or ""
        logger.info("VLM 返回: %d 字符", len(result))
        return result
