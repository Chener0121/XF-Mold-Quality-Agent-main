import asyncio
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile

from src.models.schemas.document import DocumentResponse, TaskStatusResponse
from src.services.document_service import DocumentService

router = APIRouter()

_service: DocumentService | None = None

# 内存级任务状态存储（单进程）
_tasks: dict[str, TaskStatusResponse] = {}


def _get_service() -> DocumentService:
    global _service
    if _service is None:
        _service = DocumentService()
    return _service


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile):
    """上传文档，立即返回任务 ID，后台异步处理"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".docx", ".pdf"):
        return DocumentResponse(
            id="",
            filename=file.filename,
            status="rejected: 仅支持 .docx / .pdf",
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
            # 清理临时文件
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    asyncio.create_task(_run())

    return DocumentResponse(
        id=task_id,
        filename=file.filename,
        status="processing",
    )


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询文档处理进度"""
    task = _tasks.get(task_id)
    if not task:
        return TaskStatusResponse(
            task_id=task_id,
            filename="",
            stage="not_found",
            progress={},
            status="not_found",
        )
    return task
