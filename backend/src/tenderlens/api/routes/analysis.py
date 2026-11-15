import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tenderlens.ai.embeddings import EmbeddingConfigurationError
from tenderlens.ai.llm import LLMConfigurationError
from tenderlens.analysis.service import TenderAnalysisService, TenderExtractionService
from tenderlens.config import Settings, get_settings
from tenderlens.database.session import get_session
from tenderlens.rag.service import TenderQuestionService
from tenderlens.repositories.analysis import AnalysisRepository
from tenderlens.saas.ai import tenant_llm
from tenderlens.saas.plans import entitlement
from tenderlens.saas.security import IdentityDependency, rate_limit
from tenderlens.schemas.analysis import (
    AnalysisRead,
    ExtractionRunRead,
    RequirementRead,
    TenderAnswer,
    TenderQuestion,
)

router = APIRouter(prefix="/tenders/{tender_id}", tags=["analysis"])
SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("/requirements", response_model=list[RequirementRead])
def list_requirements(tender_id: uuid.UUID, session: SessionDependency) -> list[RequirementRead]:
    return [
        RequirementRead.model_validate(item)
        for item in AnalysisRepository(session).list_requirements(tender_id)
    ]


@router.post("/extract", response_model=ExtractionRunRead)
async def extract_requirements(
    tender_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
    identity: IdentityDependency,
) -> ExtractionRunRead:
    try:
        entitlement(identity.organization, "analysis")
        rate_limit(session, f"extract:{identity.organization.id}", 30, 3600)
        llm = tenant_llm(settings, session, identity.organization)
        requirements = await TenderExtractionService(session, llm).extract(tender_id)
    except (LookupError, LLMConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if isinstance(exc, LookupError) else 503,
            detail=str(exc),
        ) from exc
    method = requirements[0].extraction_method if requirements else "rules"
    return ExtractionRunRead(
        items=[RequirementRead.model_validate(item) for item in requirements], method=method
    )


@router.get("/analysis", response_model=AnalysisRead)
def get_analysis(tender_id: uuid.UUID, session: SessionDependency) -> AnalysisRead:
    analysis = AnalysisRepository(session).get_analysis(tender_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tender analysis not generated"
        )
    return AnalysisRead.model_validate(analysis)


@router.post("/analysis", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
def generate_analysis(
    tender_id: uuid.UUID, session: SessionDependency, identity: IdentityDependency
) -> AnalysisRead:
    entitlement(identity.organization, "analysis")
    try:
        analysis = TenderAnalysisService(session).generate(tender_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AnalysisRead.model_validate(analysis)


@router.post("/ask", response_model=TenderAnswer)
async def ask_tender(
    tender_id: uuid.UUID,
    payload: TenderQuestion,
    session: SessionDependency,
    settings: SettingsDependency,
    identity: IdentityDependency,
) -> TenderAnswer:
    try:
        entitlement(identity.organization, "analysis")
        rate_limit(session, f"ask:{identity.organization.id}", 60, 3600)
        embeddings = None  # Paid query embeddings require a separate metering adapter.
        llm = tenant_llm(settings, session, identity.organization)
    except (EmbeddingConfigurationError, LLMConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return await TenderQuestionService(
        session, embedding_provider=embeddings, llm_provider=llm
    ).ask(tender_id, payload.question)
