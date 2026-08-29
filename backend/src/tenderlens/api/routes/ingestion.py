from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tenderlens.config import Settings, get_settings
from tenderlens.database.session import get_session
from tenderlens.ingestion.runner import TedIngestionRunner
from tenderlens.ingestion.ted_client import TedClient
from tenderlens.schemas.ingestion import TedIngestionRequest, TedIngestionResponse

router = APIRouter(prefix="/ingestions", tags=["ingestion"])
SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("/ted", response_model=TedIngestionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_ted(
    request: TedIngestionRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> TedIngestionResponse:
    if not settings.ted_ingestion_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TED ingestion is disabled; set TED_INGESTION_ENABLED=true to enable it.",
        )
    async with TedClient(settings) as client:
        return await TedIngestionRunner(session, client).run(request)
