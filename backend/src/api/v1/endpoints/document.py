import asyncio
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.models.schemas.document import DocumentResponse, TaskStatusResponse, DocumentListItem, AgentDocumentsRequest
from src.repositories.document_repository import DocumentRepository
from src.core.dependencies import get_db
from src.services.document_service import DocumentService
from src.document.parsers.docx_parser import DocxParser
from src.document.processors.semantic_processor import SemanticProcessor
from src.ai.rag.vectorstores.chroma_store import ChromaStore

router = APIRouter()

_service: DocumentService | None = None

# 内存级任务状态存储（单进程）
_tasks: dict[str, TaskStatusResponse] = {}


def _get_service() -> DocumentService:
    global _service
    if _service is None:
        _service = DocumentService()
    return _service


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile):
    """上传文档，立即返回任务 ID，后台异步处理"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".docx", ".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="仅支持 .docx / .pdf 格式",
        )

    # 保存上传文件
    tmp_dir = tempfile.mkdtemp(prefix="docx_upload_")
    tmp_path = Path(tmp_dir) / (file.filename or "upload.docx")
    content = await file.read()
    tmp_path.write_bytes(content)

    task_id = str(uuid.uuid4())
    task_status = TaskStatusResponse(
        task_id=task_id,
        filename=file.filename,
        stage="queued",
        progress={},
        status="processing",
    )
    _tasks[task_id] = task_status

    async def _run():
        service = _get_service()

        def on_progress(stage: str, info: dict):
            _tasks[task_id].stage = stage
            _tasks[task_id].progress = info

        try:
            result = await asyncio.to_thread(
                service.process_and_store,
                str(tmp_path),
                file.filename,
                on_progress,
            )
            _tasks[task_id].status = "completed"
            _tasks[task_id].stage = "completed"
            _tasks[task_id].progress = result
        except Exception as e:
            _tasks[task_id].status = "failed"
            _tasks[task_id].stage = _tasks[task_id].stage
            _tasks[task_id].progress = {"error": str(e)}
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    asyncio.create_task(_run())

    return DocumentResponse(
        id=task_id,
        filename=file.filename,
        status="processing",
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询文档处理进度"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.post("/analysis", response_model=dict)
async def analyze_document(file: UploadFile):
    """调试接口：解析文档到 semantic blocks，不走 VLM/embedding，用于验证 heading_path"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".docx":
        return {"error": "仅支持 .docx"}

    tmp_dir = tempfile.mkdtemp(prefix="debug_blocks_")
    tmp_path = Path(tmp_dir) / (file.filename or "upload.docx")
    tmp_path.write_bytes(await file.read())

    try:
        parser = DocxParser()
        processor = SemanticProcessor()

        elements = await asyncio.to_thread(parser.parse, str(tmp_path))
        blocks = await asyncio.to_thread(processor.process, elements, source=file.filename)

        return {
            "total_elements": len(elements),
            "total_blocks": len(blocks),
            "blocks": [
                {
                    "type": b.type,
                    "heading_path": b.metadata.get("heading_path", []),
                    "section_title": b.metadata.get("section_title", ""),
                    "is_heading": b.metadata.get("is_heading", False),
                    "content": b.content[:200],
                }
                for b in blocks
            ],
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── 文档列表 ──

@router.get("", response_model=list[DocumentListItem])
async def list_documents():
    store = ChromaStore()
    return store.list_sources()


# ── 智能体文档配置 ──

@router.get("/agents/{agent}/documents", response_model=list[str])
async def get_agent_documents(agent: str, db=Depends(get_db)):
    repo = DocumentRepository(db)
    return await repo.get_agent_documents(agent)


@router.put("/agents/{agent}/documents")
async def set_agent_documents(agent: str, body: AgentDocumentsRequest, db=Depends(get_db)):
    repo = DocumentRepository(db)
    await repo.set_agent_documents(agent, body.document_ids)
    return {"ok": True}
