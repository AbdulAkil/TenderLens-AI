import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from tenderlens.models.document import DocumentChunk, TenderDocument
from tenderlens.models.tender import Tender
from tenderlens.retrieval.types import RetrievalHit


class RetrievalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def lexical(
        self, query: str, limit: int, tender_id: uuid.UUID | None = None
    ) -> list[RetrievalHit]:
        ts_query = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(DocumentChunk.search_vector, ts_query).label("score")
        statement = self._base_statement(rank).where(DocumentChunk.search_vector.op("@@")(ts_query))
        if tender_id:
            statement = statement.where(Tender.id == tender_id)
        rows = self._session.execute(statement.order_by(rank.desc()).limit(limit)).all()
        return [self._to_hit(row, method="lexical") for row in rows]

    def semantic(
        self,
        embedding: list[float],
        limit: int,
        tender_id: uuid.UUID | None = None,
    ) -> list[RetrievalHit]:
        similarity = (1 - DocumentChunk.embedding.cosine_distance(embedding)).label("score")
        statement = self._base_statement(similarity).where(DocumentChunk.embedding.is_not(None))
        if tender_id:
            statement = statement.where(Tender.id == tender_id)
        rows = self._session.execute(statement.order_by(similarity.desc()).limit(limit)).all()
        return [self._to_hit(row, method="semantic") for row in rows]

    @staticmethod
    def _base_statement(
        score: object,
    ) -> Select[tuple[DocumentChunk, TenderDocument, Tender, float]]:
        return (
            select(DocumentChunk, TenderDocument, Tender, score)
            .join(TenderDocument, DocumentChunk.document_id == TenderDocument.id)
            .join(Tender, TenderDocument.tender_id == Tender.id)
        )

    @staticmethod
    def _to_hit(
        row: tuple[DocumentChunk, TenderDocument, Tender, float], method: str
    ) -> RetrievalHit:
        chunk, document, tender, score = row
        return RetrievalHit(
            chunk_id=chunk.id,
            tender_id=tender.id,
            document_id=document.id,
            content=chunk.content,
            source_url=document.source_url,
            score=float(score),
            page_number=chunk.page_number,
            section=chunk.section,
            method=method,
        )
