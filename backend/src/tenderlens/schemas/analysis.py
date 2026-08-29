import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    field_name: str
    value: Any
    source_document_id: uuid.UUID | None
    source_chunk_ids: list[str]
    confidence: float | None
    extraction_method: str
    extracted_at: datetime


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tender_id: uuid.UUID
    summary: str
    key_requirements: list[str]
    potential_blockers: list[str]
    required_documents: list[str]
    evaluation_criteria: list[str]
    source_chunk_ids: list[str]
    generation_method: str
    generated_at: datetime


class CitationRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    source_url: str
    page_number: int | None
    section: str | None
    excerpt: str


class TenderQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)


class TenderAnswer(BaseModel):
    answer: str
    status: str
    citations: list[CitationRead]
    retrieval_method: str
    model: str | None = None


class ExtractionRunRead(BaseModel):
    items: list[RequirementRead]
    method: str
