from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from tenderlens.saas import auth, billing, email_webhook, manual_import
from tenderlens.saas import routes as commercial
from tenderlens.saas.body_limit import BodyLimitMiddleware
from tenderlens.saas.security import current_identity, require_admin

app = FastAPI(
    title="TenderLens AI API", version="0.1.0", description="Procurement discovery foundation"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().api_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.middleware("http")(request_observability)
app.add_middleware(BodyLimitMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    settings = get_settings()
    # SameSite is defense in depth. Browser state changes must have an explicit,
    # trusted Origin; webhooks authenticate raw payloads separately.
    webhook = request.url.path in {"/api/v1/billing/webhook", "/api/v1/email/webhook"}
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not webhook:
        origin = request.headers.get("origin")
        if origin and origin not in settings.api_cors_origins:
            return JSONResponse({"detail": "Untrusted request origin"}, status_code=403)
        if request.cookies.get(settings.session_cookie) and not origin:
            return JSONResponse(
                {"detail": "Origin header required for session changes"}, status_code=403
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(auth.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(email_webhook.router, prefix="/api/v1")
app.include_router(manual_import.router, prefix="/api/v1")
app.include_router(commercial.router, prefix="/api/v1")
app.include_router(health.router)
app.include_router(analysis.router, prefix="/api/v1", dependencies=[Depends(current_identity)])
app.include_router(companies.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1", dependencies=[Depends(current_identity)])
app.include_router(embeddings.router, prefix="/api/v1", dependencies=[Depends(require_admin)])
app.include_router(ingestion.router, prefix="/api/v1", dependencies=[Depends(require_admin)])
app.include_router(matches.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1", dependencies=[Depends(current_identity)])
app.include_router(tenders.router, prefix="/api/v1")
