"""VLM 语义增强 — 将 image 类型的 SemanticBlock 通过 VLM 转换为可检索语义文本

与 parser / FastAPI / pgvector 完全解耦，纯 Python pipeline。
"""

import json

from src.core.logger import get_logger
from src.document.processors.semantic_block import SemanticBlock
from src.core.vlm_client import VLMClient

logger = get_logger(__name__)

VLM_PROMPT = """\
你是一个专业的质量管理文档分析专家，擅长分析 FMEA 和 VDA6.4 相关的图表。

请分析这张图片，完成以下任务：

1. 判断图片类型，从以下选择：
   - turtle_diagram（乌龟图）
   - flowchart（流程图）
   - structure_tree（结构树图）
   - table_screenshot（表格截图）
   - process_diagram（过程示意图）
   - other（其他）

2. 根据图片类型，深入理解业务语义：

   - 乌龟图：提取输入、输出、KPI、资源、风险、过程关系
   - 流程图：提取流程步骤、判断节点、输入输出关系、分支逻辑
   - 结构树图：提取层级关系、父子节点、分类逻辑
   - 表格截图：提取表头、数据行、关键数值
   - 过程示意图：提取过程要素、控制点、接口关系

3. 不要只做 OCR 文字提取，重点是理解：
   - 流程关系和逻辑
   - 输入输出关系
   - 关键指标（KPI）
   - 风险点和控制措施
   - 资源和约束条件
   - 业务语义和结构层级

请以 JSON 格式返回，严格遵循以下结构：
{
  "image_type": "turtle_diagram",
  "summary": "一句话概括图片核心内容",
  "content": "详细的语义描述文本，包含所有理解到的业务信息、关系和逻辑",
  "keywords": ["关键词1", "关键词2"],
  "structure": {
    "inputs": ["输入项"],
    "outputs": ["输出项"],
    "kpis": ["KPI指标"],
    "resources": ["资源"],
    "risks": ["风险点"],
    "steps": ["流程步骤"]
  }
}

其中 structure 字段根据图片类型填写相关内容，不相关的内容可以省略或留空数组。
content 字段必须详尽，将作为后续 embedding 和检索的语料。"""


def _parse_vlm_response(raw: str) -> dict:
    """解析 VLM 返回的 JSON"""
    # 尝试提取 JSON 块（VLM 可能包裹在 ```json ... ``` 中）
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉首尾的 ``` 行
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("VLM 返回非标准 JSON，降级为纯文本")
        return {"content": raw, "image_type": "other", "summary": "", "keywords": [], "structure": {}}


class VLMProcessor:
    """对 image 类型的 SemanticBlock 进行 VLM 语义增强"""

    def __init__(self, vlm_client: VLMClient | None = None):
        self.client = vlm_client or VLMClient()

    def enrich(self, block: SemanticBlock) -> SemanticBlock:
        """增强单个 image 语义块"""
        if block.type != "image":
            return block

        image_ref = block.metadata.get("image_ref")
        if not image_ref:
            logger.warning("语义块缺少 image_ref，跳过 VLM: index=%d", block.index)
            return block

        raw = self.client.analyze(image_ref, VLM_PROMPT)
        parsed = _parse_vlm_response(raw)

        # 构建新的 metadata（保留原始信息）
        new_metadata = {**block.metadata}
        if "image_type" in parsed:
            new_metadata["image_type"] = parsed["image_type"]
        if parsed.get("structure"):
            new_metadata["structure"] = parsed["structure"]

        return SemanticBlock(
            type=parsed.get("image_type", block.type),
            content=parsed.get("content", ""),
            summary=parsed.get("summary", ""),
            keywords=parsed.get("keywords", []),
            source=block.source,
            index=block.index,
            page=block.page,
            metadata=new_metadata,
        )

    def enrich_all(self, blocks: list[SemanticBlock]) -> list[SemanticBlock]:
        """批量增强所有 image 类型的语义块"""
        image_count = sum(1 for b in blocks if b.type == "image")
        logger.info("VLM 语义增强: %d 张图片待处理", image_count)

        result: list[SemanticBlock] = []
        for block in blocks:
            if block.type == "image":
                try:
                    result.append(self.enrich(block))
                except Exception:
                    logger.exception("VLM 增强失败: index=%d", block.index)
                    result.append(block)
            else:
                result.append(block)

        logger.info("VLM 语义增强完成")
        return result
