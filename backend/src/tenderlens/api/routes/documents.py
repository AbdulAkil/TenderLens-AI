import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tenderlens.config import Settings, get_settings
from tenderlens.database.session import get_session
from tenderlens.documents.processing import TenderDocumentProcessor
from tenderlens.repositories.documents import DocumentRepository
from tenderlens.schemas.document import TenderDocumentRead

router = APIRouter(prefix="/tenders/{tender_id}/documents", tags=["documents"])
SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("", response_model=list[TenderDocumentRead])
def list_documents(tender_id: uuid.UUID, session: SessionDependency) -> list[TenderDocumentRead]:
    return [
        TenderDocumentRead.model_validate(document)
        for document in DocumentRepository(session).list_for_tender(tender_id)
    ]


@router.post("/process", response_model=TenderDocumentRead, status_code=status.HTTP_201_CREATED)
async def process_document(
    tender_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
) -> TenderDocumentRead:
    if not settings.document_processing_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document processing is disabled; set DOCUMENT_PROCESSING_ENABLED=true to enable it.",
        )
    try:
        document = await TenderDocumentProcessor(session).process_notice_document(tender_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return TenderDocumentRead.model_validate(document)
