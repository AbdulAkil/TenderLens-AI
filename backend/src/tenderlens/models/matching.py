import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from tenderlens.database.base import Base


class MatchEvaluation(Base):
    """Remember rejected as well as accepted pairs so unchanged work is not repeated."""

    __tablename__ = "match_evaluations"
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenders.id", ondelete="CASCADE"), primary_key=True
    )
    profile_fingerprint: Mapped[str] = mapped_column(String(64))
    tender_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tender_version: Mapped[int] = mapped_column()
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class DigestOpportunity(Base):
    """Durable per-recipient assignment; delivery-log retention must not reset freshness."""

    __tablename__ = "digest_opportunities"
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenders.id", ondelete="CASCADE"), primary_key=True
    )
    delivery_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deliveries.id", ondelete="SET NULL"), index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("company_profiles.id", ondelete="SET NULL")
    )
    profile_fingerprint: Mapped[str | None] = mapped_column(String(64))
    tender_version: Mapped[int | None] = mapped_column()
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
