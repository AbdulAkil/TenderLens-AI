from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tenderlens.ai.embeddings import EmbeddingConfigurationError, get_embedding_provider
from tenderlens.config import Settings, get_settings
from tenderlens.database.session import get_session
from tenderlens.repositories.retrieval import RetrievalRepository
from tenderlens.retrieval.service import HybridRetriever
from tenderlens.schemas.search import SearchHit, SearchRequest, SearchResponse

router = APIRouter(tags=["search"])
SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> SearchResponse:
    try:
        provider = get_embedding_provider(settings) if request.method == "hybrid" else None
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    hits = await HybridRetriever(RetrievalRepository(session), provider).search(
        request.query,
        limit=request.limit,
        tender_id=request.tender_id,
    )
    return SearchResponse(
        items=[SearchHit.model_validate(hit) for hit in hits],
        method="hybrid" if provider else "lexical",
        semantic_enabled=provider is not None,
    )
