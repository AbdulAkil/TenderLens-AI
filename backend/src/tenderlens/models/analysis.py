import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from tenderlens.database.base import Base

if TYPE_CHECKING:
    from tenderlens.models.document import TenderDocument
    from tenderlens.models.tender import Tender


class TenderRequirement(Base):
    __tablename__ = "tender_requirements"
    __table_args__ = (
        UniqueConstraint("tender_id", "field_name", name="uq_tender_requirements_tender_field"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    field_name: Mapped[str] = mapped_column(String(128))
    value: Mapped[Any] = mapped_column(JSONB)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tender_documents.id", ondelete="SET NULL")
    )
    source_chunk_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float | None] = mapped_column()
    extraction_method: Mapped[str] = mapped_column(String(32))
    extracted_at: Mapped[datetime] = mapped_column(server_default=func.now())

    tender: Mapped["Tender"] = relationship()
    source_document: Mapped["TenderDocument | None"] = relationship()


class TenderAnalysis(Base):
    __tablename__ = "tender_analyses"

    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenders.id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str] = mapped_column(Text)
    key_requirements: Mapped[list[str]] = mapped_column(JSONB, default=list)
    potential_blockers: Mapped[list[str]] = mapped_column(JSONB, default=list)
    required_documents: Mapped[list[str]] = mapped_column(JSONB, default=list)
    evaluation_criteria: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_chunk_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    generation_method: Mapped[str] = mapped_column(String(32))
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    tender: Mapped["Tender"] = relationship()
