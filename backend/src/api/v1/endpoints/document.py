import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile

from src.models.schemas.document import DocumentResponse
from src.services.document_service import DocumentService

router = APIRouter()

# 单例（进程级）
_service: DocumentService | None = None


def _get_service() -> DocumentService:
    global _service
    if _service is None:
        _service = DocumentService()
    return _service


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile):
    """上传文档（FMEA/VDA6.4 质量手册等）"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".docx", ".pdf"):
        return DocumentResponse(
            id="",
            filename=file.filename,
            status="rejected: 仅支持 .docx / .pdf",
        )

    # 保存上传文件到临时目录
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = _get_service()
        result = service.process_and_store(tmp_path, filename=file.filename)
        return DocumentResponse(
            id="",
            filename=result["filename"],
            status=result["status"],
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
