from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from tenderlens.models.company import CompanyProfile, SavedTender, TenderMatch
from tenderlens.models.tender import Tender
from tenderlens.schemas.company import CompanyProfileCreate, CompanyProfileUpdate


class CompanyRepository:
    def __init__(self, session: Session, organization_id: uuid.UUID) -> None:
        self._session = session
        self._organization_id = organization_id

    def create(self, payload: CompanyProfileCreate) -> CompanyProfile:
        company = CompanyProfile(organization_id=self._organization_id, **payload.model_dump())
        self._session.add(company)
        self._session.commit()
        self._session.refresh(company)
        return company

    def get(self, company_id: uuid.UUID) -> CompanyProfile | None:
        return self._session.scalar(
            select(CompanyProfile).where(
                CompanyProfile.id == company_id,
                CompanyProfile.organization_id == self._organization_id,
            )
        )

    def list(self) -> list[CompanyProfile]:
        return self._session.scalars(
            select(CompanyProfile)
            .where(CompanyProfile.organization_id == self._organization_id)
            .order_by(CompanyProfile.name)
        ).all()

    def update(self, company: CompanyProfile, payload: CompanyProfileUpdate) -> CompanyProfile:
        if company.organization_id != self._organization_id:
            raise LookupError("Company profile not found")
        for field, value in payload.model_dump().items():
            setattr(company, field, value)
        self._session.commit()
        self._session.refresh(company)
        return company

    def save_tender(
        self, company_id: uuid.UUID, tender_id: uuid.UUID, notes: str | None
    ) -> SavedTender:
        if self.get(company_id) is None:
            raise LookupError("Company profile not found")
        saved = self._session.scalar(
            select(SavedTender).where(
                SavedTender.company_id == company_id, SavedTender.tender_id == tender_id
            )
        )
        if saved is None:
            saved = SavedTender(company_id=company_id, tender_id=tender_id, notes=notes)
            self._session.add(saved)
        else:
            saved.notes = notes
        self._session.commit()
        self._session.refresh(saved)
        return saved

    def list_saved(self, company_id: uuid.UUID) -> list[SavedTender]:
        if self.get(company_id) is None:
            raise LookupError("Company profile not found")
        return self._session.scalars(
            select(SavedTender)
            .where(SavedTender.company_id == company_id)
            .options(selectinload(SavedTender.tender))
            .order_by(SavedTender.created_at.desc())
        ).all()

    def list_matches(self, company_id: uuid.UUID, limit: int = 50) -> list[TenderMatch]:
        if self.get(company_id) is None:
            raise LookupError("Company profile not found")
        return self._session.scalars(
            select(TenderMatch)
            .join(Tender, TenderMatch.tender_id == Tender.id)
            .where(TenderMatch.company_id == company_id)
            .where(Tender.status.not_in(["closed", "cancelled"]))
            .where(
                (Tender.submission_deadline.is_(None))
                | (Tender.submission_deadline > datetime.now(UTC))
            )
            .options(
                selectinload(TenderMatch.tender).selectinload(Tender.cpv_codes),
                selectinload(TenderMatch.tender).selectinload(Tender.buyer),
            )
            .order_by(TenderMatch.overall_score.desc())
            .limit(limit)
        ).all()
