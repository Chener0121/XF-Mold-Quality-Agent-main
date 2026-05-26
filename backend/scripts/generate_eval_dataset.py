"""生成检索评测数据集 — 从 ChromaDB 抽样文档块，LLM 反向生成 query

用法:
    cd /app
    uv run python -m tests.generate_eval_dataset
"""

import json
import random
from pathlib import Path

import chromadb
from openai import OpenAI
from src.core.config import settings

SAMPLE_SIZE = 100
OUTPUT_PATH = Path(__file__).parent / "eval_dataset.json"

SYSTEM_PROMPT = """\
你是一位质量工程师，正在使用知识库问答系统。
请阅读以下文档片段，然后生成一个你可能会提出的中文问题。

要求:
1. 问题必须自然，像真实用户在问答系统中输入的
2. 问题必须能通过这段文档内容回答
3. 不要直接复制文档原文作为问题
4. 问题长度 10-50 字
5. 只输出问题本身，不要加编号、引号或其他格式"""

USER_TEMPLATE = """\
文档片段:
---
{content}
---

请生成一个问题:"""


def main() -> None:
    # 直接用 chromadb，绕过项目 __init__.py 循环导入
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name="semantic_blocks",
        metadata={"hnsw:space": "cosine"},
    )

    total = collection.count()
    if total == 0:
        print("ChromaDB 中没有任何文档，请先上传文档")
        return

    sample_size = min(SAMPLE_SIZE, total)
    print(f"ChromaDB 共 {total} 条文档，抽样 {sample_size} 条")

    all_data = collection.get(include=["documents"])
    all_ids = all_data["ids"]
    all_docs = all_data["documents"] or [""] * len(all_ids)

    indices = random.sample(range(len(all_ids)), sample_size)
    sampled = [(all_ids[i], all_docs[i]) for i in indices]

    # 直接用 OpenAI 客户端
    llm = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
    model = settings.LLM_MODEL
    dataset: list[dict] = []

    for idx, (block_id, content) in enumerate(sampled):
        truncated = content[:800] if len(content) > 800 else content

        try:
            resp = llm.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TEMPLATE.format(content=truncated)},
                ],
                temperature=0.7,
            )
            query = resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"  LLM 生成失败 (第 {idx + 1} 条): {e}")
            continue

        dataset.append({
            "query": query,
            "relevant_ids": [block_id],
            "source_content": content[:200],
        })

        if (idx + 1) % 10 == 0:
            print(f"  进度: {idx + 1}/{sample_size}")

    OUTPUT_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"数据集已保存: {OUTPUT_PATH} ({len(dataset)} 条)")


if __name__ == "__main__":
    main()
