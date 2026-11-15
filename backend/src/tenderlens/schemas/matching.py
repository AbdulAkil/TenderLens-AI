import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from tenderlens.schemas.tender import TenderRead


class TenderMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    tender_id: uuid.UUID
    overall_score: float
    component_scores: dict[str, float | None]
    reasons: list[str]
    blockers: list[str]
    calculated_at: datetime
    tender: TenderRead | None = None


class MatchRunRead(BaseModel):
    company_id: uuid.UUID
    calculated: int
    pending: bool = False
    items: list[TenderMatchRead]
