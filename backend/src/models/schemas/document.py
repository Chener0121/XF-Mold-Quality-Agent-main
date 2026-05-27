from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str | None = None
    status: str
    created_at: datetime | None = None


class DocumentListItem(BaseModel):
    id: str
    filename: str


class AgentDocumentsRequest(BaseModel):
    document_ids: list[str]  # 实际传的是 filename/source


class TaskStatusResponse(BaseModel):
    task_id: str
    filename: str | None = None
    stage: str  # queued / parsing / processing / enriching / embedding / completed / failed
    progress: dict[str, Any] = {}
    status: str  # processing / completed / failed / not_found
