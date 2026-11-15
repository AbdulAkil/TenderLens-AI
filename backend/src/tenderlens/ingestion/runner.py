from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from tenderlens.ingestion.normalization import normalize_ted_notice
from tenderlens.ingestion.ted_client import TedClient
from tenderlens.ingestion.tender_ingestion import TenderIngestionService
from tenderlens.schemas.ingestion import TedIngestionRequest, TedIngestionResponse

TED_DISCOVERY_FIELDS = (
    "publication-number",
    "notice-title",
    "title-proc",
    "buyer-name",
    "buyer-country",
    "publication-date",
    "deadline",
    "notice-type",
    "description-proc",
    "deadline-receipt-request",
    "deadline-receipt-tender-date-lot",
    "deadline-receipt-tender-time-lot",
    "procedure-type",
    "classification-cpv",
    "estimated-value-proc",
    "estimated-value-cur-proc",
)
logger = structlog.get_logger(__name__)


class TedIngestionRunner:
    """Coordinates bounded TED discovery and idempotent persistence."""

    def __init__(self, session: Session, client: TedClient) -> None:
        self._session = session
        self._client = client

    async def run(self, request: TedIngestionRequest) -> TedIngestionResponse:
        fetched = 0
        inserted = 0
        updated = 0
        unchanged = 0
        total_matches: int | None = None
        complete = True
        service = TenderIngestionService(self._session)

        async for page in self._client.iterate(
            query=request.query,
            fields=TED_DISCOVERY_FIELDS,
            scope=request.scope,
            limit=request.page_size,
            only_latest_versions=request.only_latest_versions,
        ):
            if total_matches is None and isinstance(page.get("totalNoticeCount"), int):
                total_matches = page["totalNoticeCount"]
            for raw_notice in page["notices"]:
                if fetched >= request.max_notices:
                    complete = False
                    break
                if not isinstance(raw_notice, dict):
                    raise ValueError("TED returned a non-object notice")
                _, created = service.upsert(normalize_ted_notice(raw_notice))
                fetched += 1
                inserted += int(created)
                updated += int(not created and service.last_upsert_changed)
                unchanged += int(not created and not service.last_upsert_changed)
            self._session.commit()
            logger.info(
                "ted_ingestion_page_committed",
                fetched=fetched,
                inserted=inserted,
                updated=updated,
                total_matches=total_matches,
            )
            if fetched >= request.max_notices:
                complete = total_matches is not None and fetched >= total_matches
                break
            if not complete:
                break

        return TedIngestionResponse(
            fetched=fetched,
            inserted=inserted,
            updated=updated,
            unchanged=unchanged,
            total_matches=total_matches,
            complete=complete,
        )
