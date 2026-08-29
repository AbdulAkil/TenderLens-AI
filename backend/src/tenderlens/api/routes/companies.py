import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tenderlens.database.session import get_session
from tenderlens.repositories.companies import CompanyRepository
from tenderlens.schemas.company import (
    CompanyProfileCreate,
    CompanyProfileRead,
    CompanyProfileUpdate,
    SavedTenderRead,
)

router = APIRouter(prefix="/companies", tags=["companies"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("", response_model=CompanyProfileRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyProfileCreate, session: SessionDependency) -> CompanyProfileRead:
    return CompanyProfileRead.model_validate(CompanyRepository(session).create(payload))


@router.get("", response_model=list[CompanyProfileRead])
def list_companies(session: SessionDependency) -> list[CompanyProfileRead]:
    return [
        CompanyProfileRead.model_validate(company) for company in CompanyRepository(session).list()
    ]


@router.get("/{company_id}", response_model=CompanyProfileRead)
def get_company(company_id: uuid.UUID, session: SessionDependency) -> CompanyProfileRead:
    company = CompanyRepository(session).get(company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found"
        )
    return CompanyProfileRead.model_validate(company)


@router.put("/{company_id}", response_model=CompanyProfileRead)
def update_company(
    company_id: uuid.UUID, payload: CompanyProfileUpdate, session: SessionDependency
) -> CompanyProfileRead:
    repository = CompanyRepository(session)
    company = repository.get(company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found"
        )
    return CompanyProfileRead.model_validate(repository.update(company, payload))


@router.get("/{company_id}/saved", response_model=list[SavedTenderRead])
def list_saved_tenders(company_id: uuid.UUID, session: SessionDependency) -> list[SavedTenderRead]:
    repository = CompanyRepository(session)
    if repository.get(company_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found"
        )
    return [SavedTenderRead.model_validate(item) for item in repository.list_saved(company_id)]
