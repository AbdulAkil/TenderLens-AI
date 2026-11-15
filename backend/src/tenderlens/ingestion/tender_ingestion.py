import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tenderlens.ingestion.normalization import NormalizedTender
from tenderlens.models.buyer import Buyer
from tenderlens.models.tender import Tender, TenderCpvCode
from tenderlens.saas.models import NoticeRevision


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
        if tender is not None and tender.raw_metadata == notice.raw_metadata:
            return tender, False
        previous = tender.raw_metadata if tender else {}
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
        content_hash = hashlib.sha256(
            json.dumps(notice.raw_metadata, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        revision = self._session.scalar(
            select(NoticeRevision).where(
                NoticeRevision.tender_id == tender.id, NoticeRevision.content_hash == content_hash
            )
        )
        if revision is None:
            changes = {
                key: {"previous": previous.get(key), "current": value}
                for key, value in notice.raw_metadata.items()
                if previous.get(key) != value
            }
            self._session.add(
                NoticeRevision(
                    tender_id=tender.id,
                    content_hash=content_hash,
                    raw_metadata=notice.raw_metadata,
                    changes=changes,
                )
            )
        tender.source_last_updated_at = now
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
