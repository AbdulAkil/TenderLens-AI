from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from tenderlens.database.session import get_session
from tenderlens.ingestion.normalization import NormalizedTender
from tenderlens.ingestion.tender_ingestion import TenderIngestionService
from tenderlens.saas.email import safe_link
from tenderlens.saas.security import audit, require_admin

router = APIRouter(prefix="/admin", tags=["manual official-source import"])


class ManualNotice(BaseModel):
    source_id: str = Field(min_length=1, max_length=128)
    source_url: str = Field(max_length=2048)
    title: str = Field(min_length=3, max_length=2000)
    description: str | None = Field(default=None, max_length=50000)
    buyer_name: str | None = Field(default=None, max_length=256)
    buyer_country_code: str | None = Field(default=None, max_length=3)
    submission_deadline: datetime | None = None
    publication_date: datetime | None = None
    estimated_value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    cpv_codes: list[str] = Field(default_factory=list, max_length=100)
    confirmed_authorized_reuse: bool
    status: Literal["unknown", "open", "closed", "cancelled"] = "unknown"


@router.post("/imports", status_code=201)
def import_notice(
    payload: ManualNotice,
    identity: Annotated[object, Depends(require_admin)],
    session: Annotated[Session, Depends(get_session)],
):
    if not payload.confirmed_authorized_reuse or not safe_link(payload.source_url):
        raise HTTPException(
            422, "Confirm permitted reuse and provide a recognized official HTTPS source URL"
        )
    for value in [payload.publication_date, payload.submission_deadline]:
        if value and value.tzinfo is None:
            raise HTTPException(
                422, "Provide timezone-aware source timestamps; leave unknown values empty"
            )
    source = "ted" if urlsplit(payload.source_url).hostname == "ted.europa.eu" else "belgian_manual"
    raw = payload.model_dump(mode="json")
    raw["manual_import"] = True
    notice = NormalizedTender(
        source=source,
        status=payload.status,
        source_id=payload.source_id,
        source_url=payload.source_url,
        title=payload.title,
        description=payload.description,
        buyer_name=payload.buyer_name,
        buyer_country_code=payload.buyer_country_code,
        submission_deadline=payload.submission_deadline,
        publication_date=payload.publication_date,
        estimated_value=payload.estimated_value,
        currency=payload.currency,
        cpv_codes=tuple(payload.cpv_codes),
        raw_metadata=raw,
    )
    tender, created = TenderIngestionService(session).upsert(notice)
    audit(
        session,
        identity,
        "official_notice_imported",
        {"tender_id": str(tender.id), "source": source},
    )
    session.commit()
    return {"tender_id": str(tender.id), "created": created}
