from fastapi import APIRouter, UploadFile

from src.models.schemas.common import PageResponse
from src.models.schemas.document import DocumentResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile):
    """上传文档（FMEA/VDA6.4 质量手册等）"""
    # TODO: 接入文档处理流水线
    return DocumentResponse(id="0", filename=file.filename, status="uploaded")


@router.get("", response_model=PageResponse[DocumentResponse])
async def list_documents():
    """获取文档列表"""
    # TODO: 接入文档仓库
    return PageResponse(items=[], total=0)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """获取文档详情"""
    # TODO: 接入文档仓库
    pass


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    # TODO: 接入文档仓库
    pass
