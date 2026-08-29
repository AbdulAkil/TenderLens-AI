import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalHit:
    chunk_id: uuid.UUID
    tender_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    source_url: str
    score: float
    page_number: int | None
    section: str | None
    method: str
