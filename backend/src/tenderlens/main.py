from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tenderlens.api.routes import (
    analysis,
    companies,
    documents,
    embeddings,
    health,
    ingestion,
    matches,
    search,
    tenders,
)
from tenderlens.common.observability import request_observability
from tenderlens.config import get_settings

app = FastAPI(
    title="TenderLens AI API", version="0.1.0", description="Procurement discovery foundation"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().api_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.middleware("http")(request_observability)
app.include_router(health.router)
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(embeddings.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(tenders.router, prefix="/api/v1")
