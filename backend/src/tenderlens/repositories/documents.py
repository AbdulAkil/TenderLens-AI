import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from tenderlens.models.document import TenderDocument


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_tender(self, tender_id: uuid.UUID) -> list[TenderDocument]:
        return self._session.scalars(
            select(TenderDocument)
            .where(TenderDocument.tender_id == tender_id)
            .options(selectinload(TenderDocument.chunks))
            .order_by(TenderDocument.created_at)
        ).all()
