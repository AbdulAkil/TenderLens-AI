import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from tenderlens.models.analysis import TenderAnalysis, TenderRequirement
from tenderlens.models.document import DocumentChunk, TenderDocument
from tenderlens.models.tender import Tender


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def tender_with_evidence(self, tender_id: uuid.UUID) -> Tender | None:
        return self._session.scalar(
            select(Tender)
            .where(Tender.id == tender_id)
            .options(
                selectinload(Tender.documents).selectinload(TenderDocument.chunks),
                selectinload(Tender.cpv_codes),
                selectinload(Tender.buyer),
            )
        )

    def list_requirements(self, tender_id: uuid.UUID) -> list[TenderRequirement]:
        return self._session.scalars(
            select(TenderRequirement)
            .where(TenderRequirement.tender_id == tender_id)
            .order_by(TenderRequirement.field_name)
        ).all()

    def replace_requirements(
        self, tender_id: uuid.UUID, requirements: list[TenderRequirement]
    ) -> list[TenderRequirement]:
        self._session.execute(
            delete(TenderRequirement).where(TenderRequirement.tender_id == tender_id)
        )
        self._session.add_all(requirements)
        self._session.commit()
        for requirement in requirements:
            self._session.refresh(requirement)
        return requirements

    def get_analysis(self, tender_id: uuid.UUID) -> TenderAnalysis | None:
        return self._session.get(TenderAnalysis, tender_id)

    def upsert_analysis(self, analysis: TenderAnalysis) -> TenderAnalysis:
        existing = self._session.get(TenderAnalysis, analysis.tender_id)
        if existing is None:
            self._session.add(analysis)
            result = analysis
        else:
            for field in (
                "summary",
                "key_requirements",
                "potential_blockers",
                "required_documents",
                "evaluation_criteria",
                "source_chunk_ids",
                "generation_method",
            ):
                setattr(existing, field, getattr(analysis, field))
            result = existing
        self._session.commit()
        self._session.refresh(result)
        return result

    def chunks_for_tender(self, tender_id: uuid.UUID) -> list[tuple[DocumentChunk, TenderDocument]]:
        return self._session.execute(
            select(DocumentChunk, TenderDocument)
            .join(TenderDocument, DocumentChunk.document_id == TenderDocument.id)
            .where(TenderDocument.tender_id == tender_id)
            .order_by(DocumentChunk.chunk_index)
        ).all()
