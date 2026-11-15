import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from tenderlens.database.session import get_session
from tenderlens.ranking.matching import MatchService
from tenderlens.repositories.companies import CompanyRepository
from tenderlens.saas.plans import entitlement
from tenderlens.saas.security import IdentityDependency
from tenderlens.schemas.matching import MatchRunRead, TenderMatchRead

router = APIRouter(prefix="/companies/{company_id}/matches", tags=["matching"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/recalculate", response_model=MatchRunRead, status_code=status.HTTP_201_CREATED)
def recalculate_matches(
    company_id: uuid.UUID, session: SessionDependency, identity: IdentityDependency
) -> MatchRunRead:
    entitlement(identity.organization)
    if CompanyRepository(session, identity.organization.id).get(company_id) is None:
        raise HTTPException(404, "Company profile not found")
    try:
        matches = MatchService(session).calculate_for_company(company_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MatchRunRead(
        company_id=company_id,
        calculated=len(matches),
        items=[TenderMatchRead.model_validate(item) for item in matches],
    )


@router.get("", response_model=list[TenderMatchRead])
def list_matches(
    company_id: uuid.UUID,
    session: SessionDependency,
    identity: IdentityDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[TenderMatchRead]:
    repository = CompanyRepository(session, identity.organization.id)
    if repository.get(company_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found"
        )
    return [
        TenderMatchRead.model_validate(item) for item in repository.list_matches(company_id, limit)
    ]
