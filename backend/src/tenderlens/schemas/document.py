import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenderDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_url: str
    file_name: str | None
    media_type: str | None
    processing_status: str
    extracted_at: datetime | None
    chunk_count: int
