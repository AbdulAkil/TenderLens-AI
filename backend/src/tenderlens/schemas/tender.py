import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TenderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    source_id: str
    source_url: str
    title: str
    description: str | None
    country_code: str | None
    region_code: str | None
    publication_date: datetime | None
    submission_deadline: datetime | None
    estimated_value: Decimal | None
    currency: str | None
    procedure_type: str | None
    buyer_name: str | None
    cpv_code_values: list[str]


class TenderPage(BaseModel):
    items: list[TenderRead]
    limit: int
    offset: int
    total: int


class TenderComparisonRequest(BaseModel):
    tender_ids: list[uuid.UUID] = Field(min_length=2, max_length=4)


class TenderComparisonRead(BaseModel):
    items: list[TenderRead]
