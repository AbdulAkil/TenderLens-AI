import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1_000)
    tender_id: uuid.UUID | None = None
    limit: int = Field(default=10, ge=1, le=50)
    method: Literal["lexical", "hybrid"] = "hybrid"


class SearchHit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: uuid.UUID
    tender_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    source_url: str
    score: float
    page_number: int | None
    section: str | None
    method: str


class SearchResponse(BaseModel):
    items: list[SearchHit]
    method: str
    semantic_enabled: bool
