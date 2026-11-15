import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tenderlens.database.base import Base
from tenderlens.models.timestamps import TimestampMixin

if TYPE_CHECKING:
    from tenderlens.models.buyer import Buyer
    from tenderlens.models.document import TenderDocument


class Tender(TimestampMixin, Base):
    __tablename__ = "tenders"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_tenders_source_source_id"),
        Index("ix_tenders_matching_updated", "updated_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(24), default="unknown")
    match_version: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": match_version}
    source_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("buyers.id"))
    country_code: Mapped[str | None] = mapped_column(String(3))
    region_code: Mapped[str | None] = mapped_column(String(16))
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submission_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    procedure_type: Mapped[str | None] = mapped_column(String(128))
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_last_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    buyer: Mapped["Buyer | None"] = relationship(back_populates="tenders")
    documents: Mapped[list["TenderDocument"]] = relationship(back_populates="tender")
    cpv_codes: Mapped[list["TenderCpvCode"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )

    @property
    def buyer_name(self) -> str | None:
        return self.buyer.name if self.buyer is not None else None

    @property
    def cpv_code_values(self) -> list[str]:
        return [cpv.code for cpv in self.cpv_codes]


class TenderCpvCode(Base):
    __tablename__ = "tender_cpv_codes"

    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenders.id", ondelete="CASCADE"), primary_key=True
    )
    code: Mapped[str] = mapped_column(String(8), primary_key=True)

    tender: Mapped["Tender"] = relationship(back_populates="cpv_codes")
