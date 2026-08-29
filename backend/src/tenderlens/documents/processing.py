from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tenderlens.documents.chunking import chunk_text
from tenderlens.documents.downloader import DocumentDownloader
from tenderlens.documents.extraction import extract_text
from tenderlens.documents.source import preferred_notice_document
from tenderlens.models.document import DocumentChunk, TenderDocument
from tenderlens.models.tender import Tender


class TenderDocumentProcessor:
    """Registers and processes the official notice document for one tender.

    This milestone processes the notice's XML or HTML representation only. It
    intentionally does not crawl external procurement-platform attachments.
    """

    def __init__(self, session: Session, downloader: DocumentDownloader | None = None) -> None:
        self._session = session
        self._downloader = downloader or DocumentDownloader()

    async def process_notice_document(self, tender_id: uuid.UUID) -> TenderDocument:
        tender = self._session.get(Tender, tender_id)
        if tender is None:
            raise LookupError("Tender not found")
        source = preferred_notice_document(tender.raw_metadata)
        if source is None:
            raise LookupError("Tender has no supported official notice document URL")

        document = self._session.scalar(
            select(TenderDocument).where(
                TenderDocument.tender_id == tender.id,
                TenderDocument.source_url == source.url,
            )
        )
        if document is None:
            document = TenderDocument(
                tender_id=tender.id,
                source_url=source.url,
                media_type=source.media_type,
                processing_status="processing",
            )
            self._session.add(document)
            self._session.flush()
        else:
            document.processing_status = "processing"
            document.media_type = source.media_type

        try:
            content, response_media_type = await self._downloader.download(source.url)
            document.media_type = response_media_type or source.media_type
            text = extract_text(content, document.media_type, source.url)
            document.chunks = [
                DocumentChunk(
                    content=chunk.content, chunk_index=chunk.chunk_index, section=chunk.section
                )
                for chunk in chunk_text(text)
            ]
            document.processing_status = "completed"
            document.extracted_at = datetime.now(UTC)
            self._session.commit()
        except Exception:
            document_id = document.id
            self._session.rollback()
            failed_document = self._session.get(TenderDocument, document_id)
            if failed_document is None:
                failed_document = TenderDocument(
                    tender_id=tender.id,
                    source_url=source.url,
                    media_type=source.media_type,
                    processing_status="failed",
                )
                self._session.add(failed_document)
            else:
                failed_document.processing_status = "failed"
            self._session.commit()
            raise
        return document
