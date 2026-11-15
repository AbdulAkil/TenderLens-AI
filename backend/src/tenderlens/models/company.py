import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from tenderlens.database.base import Base
from tenderlens.models.timestamps import TimestampMixin

if TYPE_CHECKING:
    from tenderlens.models.tender import Tender


class CompanyProfile(TimestampMixin, Base):
    __tablename__ = "company_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    website: Mapped[str | None] = mapped_column(String(2048))
    exclusions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    tender_types: Mapped[list[str]] = mapped_column(JSONB, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    services: Mapped[list[str]] = mapped_column(JSONB, default=list)
    industries: Mapped[list[str]] = mapped_column(JSONB, default=list)
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSONB, default=list)
    preferred_locations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    cpv_codes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=list)
    minimum_contract_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    maximum_contract_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    company_size: Mapped[str | None] = mapped_column(String(64))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    saved_tenders: Mapped[list["SavedTender"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    matches: Mapped[list["TenderMatch"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class SavedTender(Base):
    __tablename__ = "saved_tenders"
    __table_args__ = (
        UniqueConstraint("company_id", "tender_id", name="uq_saved_tenders_company_tender"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company_profiles.id", ondelete="CASCADE")
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    company: Mapped[CompanyProfile] = relationship(back_populates="saved_tenders")
    tender: Mapped["Tender"] = relationship()


class TenderMatch(Base):
    __tablename__ = "tender_matches"
    __table_args__ = (
        UniqueConstraint("company_id", "tender_id", name="uq_tender_matches_company_tender"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company_profiles.id", ondelete="CASCADE")
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    overall_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    component_scores: Mapped[dict[str, float | None]] = mapped_column(JSONB)
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list)
    blockers: Mapped[list[str]] = mapped_column(JSONB, default=list)
    calculated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    company: Mapped[CompanyProfile] = relationship(back_populates="matches")
    tender: Mapped["Tender"] = relationship()
