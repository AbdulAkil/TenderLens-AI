import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from tenderlens.models.buyer import Buyer
from tenderlens.models.tender import Tender


class TenderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
        country: str | None = None,
        cpv: str | None = None,
        buyer: str | None = None,
        min_value: Decimal | None = None,
        max_value: Decimal | None = None,
        deadline_before: datetime | None = None,
        published_after: datetime | None = None,
    ) -> tuple[list[Tender], int]:
        statement = select(Tender).options(
            selectinload(Tender.buyer), selectinload(Tender.cpv_codes)
        )
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(Tender.title.ilike(pattern), Tender.description.ilike(pattern))
            )
        if country:
            statement = statement.where(Tender.country_code == country.upper())
        if cpv:
            statement = statement.where(Tender.cpv_codes.any(code=cpv))
        if buyer:
            statement = statement.join(Buyer).where(Buyer.name.ilike(f"%{buyer.strip()}%"))
        if min_value is not None:
            statement = statement.where(Tender.estimated_value >= min_value)
        if max_value is not None:
            statement = statement.where(Tender.estimated_value <= max_value)
        if deadline_before is not None:
            statement = statement.where(Tender.submission_deadline <= deadline_before)
        if published_after is not None:
            statement = statement.where(Tender.publication_date >= published_after)
        records = self._session.scalars(
            statement.order_by(Tender.publication_date.desc().nullslast())
            .limit(limit)
            .offset(offset)
        ).all()
        total = self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        return records, total

    def get(self, tender_id: uuid.UUID) -> Tender | None:
        return self._session.get(Tender, tender_id)
