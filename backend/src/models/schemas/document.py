from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str | None = None
    status: str
    created_at: datetime | None = None
