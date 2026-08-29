from datetime import UTC, datetime

from fastapi import APIRouter

from tenderlens.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="tenderlens-api", timestamp=datetime.now(UTC))
