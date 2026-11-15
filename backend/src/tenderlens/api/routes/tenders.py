import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tenderlens.database.session import get_session
from tenderlens.models.company import CompanyProfile, SavedTender
from tenderlens.repositories.companies import CompanyRepository
from tenderlens.repositories.tenders import TenderRepository
from tenderlens.saas.plans import entitlement
from tenderlens.saas.security import IdentityDependency
from tenderlens.schemas.company import SavedTenderCreate, SavedTenderRead
from tenderlens.schemas.tender import (
    TenderComparisonRead,
    TenderComparisonRequest,
    TenderPage,
    TenderRead,
)

router = APIRouter(prefix="/tenders", tags=["tenders"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/compare", response_model=TenderComparisonRead)
def compare_tenders(
    payload: TenderComparisonRequest, session: SessionDependency, identity: IdentityDependency
) -> TenderComparisonRead:
    entitlement(identity.organization, "comparison")
    repository = TenderRepository(session)
    tenders = [repository.get(tender_id) for tender_id in payload.tender_ids]
    if any(tender is None for tender in tenders):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="One or more tenders were not found"
        )
    return TenderComparisonRead(items=[TenderRead.model_validate(tender) for tender in tenders])


@router.get("", response_model=TenderPage)
def list_tenders(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[str | None, Query(min_length=2, max_length=500)] = None,
    country: Annotated[str | None, Query(min_length=2, max_length=3)] = None,
    cpv: Annotated[str | None, Query(min_length=2, max_length=8)] = None,
    buyer: Annotated[str | None, Query(min_length=2, max_length=256)] = None,
    min_value: Annotated[Decimal | None, Query(ge=0)] = None,
    max_value: Annotated[Decimal | None, Query(ge=0)] = None,
    deadline_before: datetime | None = None,
    published_after: datetime | None = None,
) -> TenderPage:
    items, total = TenderRepository(session).list(
        limit=limit,
        offset=offset,
        query=query,
        country=country,
        cpv=cpv,
        buyer=buyer,
        min_value=min_value,
        max_value=max_value,
        deadline_before=deadline_before,
        published_after=published_after,
    )
    return TenderPage(
        items=[TenderRead.model_validate(item) for item in items],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/{tender_id}", response_model=TenderRead)
def get_tender(tender_id: uuid.UUID, session: SessionDependency) -> TenderRead:
    tender = TenderRepository(session).get(tender_id)
    if tender is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")
    return TenderRead.model_validate(tender)


@router.post(
    "/{tender_id}/save", response_model=SavedTenderRead, status_code=status.HTTP_201_CREATED
)
def save_tender(
    tender_id: uuid.UUID,
    payload: SavedTenderCreate,
    session: SessionDependency,
    identity: IdentityDependency,
) -> SavedTenderRead:
    if TenderRepository(session).get(tender_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")
    plan = entitlement(identity.organization)
    session.refresh(identity.organization, with_for_update=True)
    repository = CompanyRepository(session, identity.organization.id)
    if repository.get(payload.company_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found"
        )
    existing = session.scalar(
        select(SavedTender).where(
            SavedTender.company_id == payload.company_id, SavedTender.tender_id == tender_id
        )
    )
    count = session.scalar(
        select(func.count())
        .select_from(SavedTender)
        .join(CompanyProfile)
        .where(CompanyProfile.organization_id == identity.organization.id)
    )
    if not existing and count >= plan.saved:
        raise HTTPException(403, "Saved opportunity limit reached for your plan")
    return SavedTenderRead.model_validate(
        repository.save_tender(payload.company_id, tender_id, payload.notes)
    )
