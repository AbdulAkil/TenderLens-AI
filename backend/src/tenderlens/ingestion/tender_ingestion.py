from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tenderlens.ingestion.normalization import NormalizedTender
from tenderlens.models.buyer import Buyer
from tenderlens.models.tender import Tender, TenderCpvCode


class TenderIngestionService:
    """Idempotently persists a normalized notice without coupling it to HTTP routes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, notice: NormalizedTender) -> tuple[Tender, bool]:
        tender = self._session.scalar(
            select(Tender).where(
                Tender.source == notice.source, Tender.source_id == notice.source_id
            )
        )
        now = datetime.now(UTC)
        buyer = self._get_or_create_buyer(notice)
        if tender is None:
            tender = Tender(
                source=notice.source,
                source_id=notice.source_id,
                source_url=notice.source_url,
                title=notice.title,
                description=notice.description,
                buyer=buyer,
                country_code=notice.buyer_country_code,
                raw_metadata=notice.raw_metadata,
                publication_date=notice.publication_date,
                submission_deadline=notice.submission_deadline,
                estimated_value=notice.estimated_value,
                currency=notice.currency,
                procedure_type=notice.procedure_type,
                ingested_at=now,
            )
            tender.cpv_codes = [TenderCpvCode(code=code) for code in notice.cpv_codes]
            self._session.add(tender)
            created = True
        else:
            tender.source_url = notice.source_url
            tender.title = notice.title
            tender.description = notice.description
            tender.buyer = buyer
            tender.country_code = notice.buyer_country_code
            tender.raw_metadata = notice.raw_metadata
            tender.publication_date = notice.publication_date
            tender.submission_deadline = notice.submission_deadline
            tender.estimated_value = notice.estimated_value
            tender.currency = notice.currency
            tender.procedure_type = notice.procedure_type
            tender.ingested_at = now
            tender.cpv_codes = [TenderCpvCode(code=code) for code in notice.cpv_codes]
            created = False
        self._session.flush()
        return tender, created

    def _get_or_create_buyer(self, notice: NormalizedTender) -> Buyer | None:
        if not notice.buyer_name:
            return None
        buyer = self._session.scalar(
            select(Buyer).where(
                Buyer.name == notice.buyer_name,
                Buyer.country_code == notice.buyer_country_code,
            )
        )
        if buyer is None:
            buyer = Buyer(name=notice.buyer_name, country_code=notice.buyer_country_code)
            self._session.add(buyer)
            self._session.flush()
        return buyer
