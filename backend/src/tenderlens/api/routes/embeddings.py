import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tenderlens.ai.embedding_jobs import EmbeddingJob
from tenderlens.ai.embeddings import EmbeddingConfigurationError, get_embedding_provider
from tenderlens.config import Settings, get_settings
from tenderlens.database.session import get_session
from tenderlens.schemas.embeddings import EmbeddingJobResponse

router = APIRouter(prefix="/tenders/{tender_id}/embeddings", tags=["embeddings"])
SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("", response_model=EmbeddingJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def embed_tender(
    tender_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
) -> EmbeddingJobResponse:
    if not settings.embedding_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding is disabled; configure a provider and set EMBEDDING_ENABLED=true.",
        )
    try:
        provider = get_embedding_provider(settings)
    except EmbeddingConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No embedding provider is configured.",
        )
    return EmbeddingJobResponse(
        embedded_chunks=await EmbeddingJob(session, provider).embed_tender_chunks(tender_id)
    )
