from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from tenderlens.database.session import get_session
from tenderlens.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="tenderlens-api", timestamp=datetime.now(UTC))


@router.get("/ready")
def ready(session: Annotated[Session, Depends(get_session)]):
    try:
        session.execute(text("SELECT 1"))
        revision = session.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if revision != "20261115_0007":
            raise ValueError("Migrations required")
    except Exception:
        raise HTTPException(503, "Database is unavailable or migrations are pending") from None
    return {"status": "ready"}
