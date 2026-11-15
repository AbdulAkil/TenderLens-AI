import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from tenderlens.config import get_settings
from tenderlens.database.session import get_session
from tenderlens.models.company import SavedTender
from tenderlens.models.tender import Tender
from tenderlens.repositories.companies import CompanyRepository
from tenderlens.saas.models import (
    Delivery,
    Job,
    Membership,
    NotificationPreference,
    Organization,
    PilotLead,
    TenderFeedback,
    UsageRecord,
    User,
)
from tenderlens.saas.plans import entitlement
from tenderlens.saas.security import (
    IdentityDependency,
    audit,
    rate_limit,
    request_key,
    require_admin,
    require_manager,
)

router = APIRouter(tags=["commercial workspace"])
DB = Annotated[Session, Depends(get_session)]


class Preferences(BaseModel):
    frequency: Literal["off", "weekly", "daily"] = "weekly"
    minimum_score: int = Field(default=40, ge=0, le=100)
    deadline_reminders: bool = True
    updates: bool = True
    timezone: str = "Europe/Brussels"

    @field_validator("timezone")
    @classmethod
    def timezone_exists(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError("Choose a valid IANA timezone") from None
        return value


@router.get("/notifications/preferences", response_model=Preferences)
def get_preferences(identity: IdentityDependency, session: DB):
    row = session.get(NotificationPreference, (identity.user.id, identity.organization.id))
    return Preferences.model_validate(row, from_attributes=True) if row else Preferences()


@router.put("/notifications/preferences", response_model=Preferences)
def update_preferences(payload: Preferences, identity: IdentityDependency, session: DB):
    entitlement(identity.organization, "daily" if payload.frequency == "daily" else None)
    row = session.get(NotificationPreference, (identity.user.id, identity.organization.id))
    if row is None:
        row = NotificationPreference(
            user_id=identity.user.id, organization_id=identity.organization.id
        )
        session.add(row)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    audit(session, identity, "notification_preferences_changed", payload.model_dump())
    session.commit()
    return payload


@router.get("/notifications/history")
def delivery_history(identity: IdentityDependency, session: DB):
    rows = session.scalars(
        select(Delivery)
        .where(
            Delivery.organization_id == identity.organization.id,
            Delivery.user_id == identity.user.id,
        )
        .order_by(Delivery.created_at.desc())
        .limit(50)
    ).all()
    return [
        {
            "id": str(row.id),
            "category": row.category,
            "subject": row.subject,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


class FeedbackInput(BaseModel):
    value: Literal[
        "relevant", "irrelevant", "interested", "not_eligible", "applied", "not_interested"
    ]


@router.put("/companies/{company_id}/feedback/{tender_id}")
def feedback(
    company_id: uuid.UUID,
    tender_id: uuid.UUID,
    payload: FeedbackInput,
    identity: IdentityDependency,
    session: DB,
):
    if CompanyRepository(session, identity.organization.id).get(company_id) is None:
        raise HTTPException(404, "Company profile not found")
    if session.get(Tender, tender_id) is None:
        raise HTTPException(404, "Tender not found")
    row = session.scalar(
        select(TenderFeedback).where(
            TenderFeedback.company_id == company_id, TenderFeedback.tender_id == tender_id
        )
    )
    if not row:
        row = TenderFeedback(company_id=company_id, tender_id=tender_id)
        session.add(row)
    row.value = payload.value
    session.commit()
    return {"message": "Feedback saved. Dismissed tenders are excluded from future digests."}


@router.delete("/companies/{company_id}/saved/{tender_id}")
def unsave(company_id: uuid.UUID, tender_id: uuid.UUID, identity: IdentityDependency, session: DB):
    if CompanyRepository(session, identity.organization.id).get(company_id) is None:
        raise HTTPException(404, "Company profile not found")
    session.execute(
        delete(SavedTender).where(
            SavedTender.company_id == company_id, SavedTender.tender_id == tender_id
        )
    )
    session.commit()
    return {"message": "Opportunity removed"}


@router.get("/account/team")
def team(identity: IdentityDependency, session: DB):
    rows = session.execute(
        select(User, Membership)
        .join(Membership)
        .where(Membership.organization_id == identity.organization.id)
    ).all()
    return [
        {"user_id": str(user.id), "email": user.email, "role": member.role} for user, member in rows
    ]


class MemberInput(BaseModel):
    email: EmailStr
    role: Literal["admin", "member"] = "member"


@router.post("/account/team", status_code=201)
def add_member(payload: MemberInput, identity: IdentityDependency, session: DB):
    require_manager(identity)
    plan = entitlement(identity.organization)
    session.refresh(identity.organization, with_for_update=True)
    count = session.scalar(
        select(func.count())
        .select_from(Membership)
        .where(Membership.organization_id == identity.organization.id)
    )
    if count >= plan.members:
        raise HTTPException(403, "Team member limit reached")
    user = session.scalar(
        select(User).where(User.email == str(payload.email).lower(), User.verified.is_(True))
    )
    if not user:
        raise HTTPException(404, "Ask this person to create and verify a TenderLens account first")
    if session.get(Membership, (user.id, identity.organization.id)):
        raise HTTPException(409, "Already a team member")
    session.add(
        Membership(user_id=user.id, organization_id=identity.organization.id, role=payload.role)
    )
    session.add(NotificationPreference(user_id=user.id, organization_id=identity.organization.id))
    audit(session, identity, "member_added", {"user_id": str(user.id), "role": payload.role})
    session.commit()
    return {"message": "Member added. They can switch organizations from account settings."}


@router.delete("/account/team/{user_id}")
def remove_member(user_id: uuid.UUID, identity: IdentityDependency, session: DB):
    require_manager(identity)
    member = session.get(Membership, (user_id, identity.organization.id))
    if not member or member.role == "owner":
        raise HTTPException(403, "Organization owner cannot be removed")
    session.delete(member)
    session.execute(
        delete(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.organization_id == identity.organization.id,
        )
    )
    audit(session, identity, "member_removed", {"user_id": str(user_id)})
    session.commit()
    return {"message": "Member removed and organization access revoked"}


@router.get("/account/organizations")
def organizations(identity: IdentityDependency, session: DB):
    rows = session.scalars(
        select(Organization)
        .join(Membership)
        .where(Membership.user_id == identity.user.id, Organization.deletion_requested_at.is_(None))
    ).all()
    return [{"id": str(row.id), "name": row.name} for row in rows]


class SwitchInput(BaseModel):
    organization_id: uuid.UUID


@router.post("/account/switch")
def switch_organization(
    payload: SwitchInput, request: Request, identity: IdentityDependency, session: DB
):
    from tenderlens.saas.models import AuthSession
    from tenderlens.saas.security import token_hash

    org = session.get(Organization, payload.organization_id)
    if (
        not org
        or org.deletion_requested_at
        or not session.get(Membership, (identity.user.id, org.id))
    ):
        raise HTTPException(404, "Organization not found")
    auth = session.get(AuthSession, token_hash(request.cookies[get_settings().session_cookie]))
    auth.organization_id = org.id
    session.commit()
    return {"message": "Organization switched"}


@router.get("/account/export")
def export(identity: IdentityDependency, session: DB):
    # A user's privacy export is available even when the subscription has expired.
    from tenderlens.schemas.company import CompanyProfileRead

    companies = CompanyRepository(session, identity.organization.id).list()
    ids = [company.id for company in companies]
    return {
        "email": identity.user.email,
        "organization": identity.organization.name,
        "role": identity.role,
        "profiles": [
            CompanyProfileRead.model_validate(company).model_dump(mode="json")
            for company in companies
        ],
        "saved": [
            {"company_id": str(row.company_id), "tender_id": str(row.tender_id), "notes": row.notes}
            for row in session.scalars(select(SavedTender).where(SavedTender.company_id.in_(ids)))
        ],
        "feedback": [
            {"company_id": str(row.company_id), "tender_id": str(row.tender_id), "value": row.value}
            for row in session.scalars(
                select(TenderFeedback).where(TenderFeedback.company_id.in_(ids))
            )
        ],
        "preferences": get_preferences(identity, session).model_dump(),
        "deliveries": delivery_history(identity, session),
    }


class LeadInput(BaseModel):
    email: EmailStr
    company_name: str = Field(min_length=2, max_length=256)
    message: str = Field(min_length=5, max_length=2000)
    consent_to_contact: bool


@router.post("/pilot-interest", status_code=202)
def pilot_interest(payload: LeadInput, request: Request, session: DB):
    rate_limit(session, request_key(request, "lead"), 3)
    if not payload.consent_to_contact:
        raise HTTPException(422, "Consent to a response is required")
    if not session.scalar(select(PilotLead).where(PilotLead.email == str(payload.email).lower())):
        session.add(
            PilotLead(
                email=str(payload.email).lower(),
                company_name=payload.company_name,
                message=payload.message,
            )
        )
        session.commit()
    return {
        "message": "Your pilot request has been recorded. No marketing emails are sent automatically."
    }


@router.get("/admin/overview")
def admin_overview(identity: Annotated[object, Depends(require_admin)], session: DB):
    counts = {
        "organizations": session.scalar(select(func.count()).select_from(Organization)),
        "tenders": session.scalar(select(func.count()).select_from(Tender)),
        "pending_review": session.scalar(
            select(func.count()).select_from(Delivery).where(Delivery.status == "review")
        ),
        "failed_jobs": session.scalar(
            select(func.count()).select_from(Job).where(Job.status == "failed")
        ),
    }
    jobs = session.scalars(select(Job).order_by(Job.created_at.desc()).limit(30)).all()
    deliveries = session.scalars(
        select(Delivery)
        .where(Delivery.category.not_in(["verify", "reset"]))
        .order_by(Delivery.created_at.desc())
        .limit(30)
    ).all()
    organizations = session.scalars(
        select(Organization).order_by(Organization.created_at.desc()).limit(100)
    ).all()
    return {
        "counts": counts,
        "jobs": [
            {
                "id": str(row.id),
                "kind": row.kind,
                "status": row.status,
                "attempts": row.attempts,
                "last_error": row.last_error,
                "result": row.result,
            }
            for row in jobs
        ],
        "deliveries": [
            {
                "id": str(row.id),
                "subject": row.subject,
                "status": row.status,
                "organization_id": str(row.organization_id),
            }
            for row in deliveries
        ],
        "organizations": [
            {
                "id": str(row.id),
                "name": row.name,
                "plan": row.plan,
                "status": row.subscription_status,
            }
            for row in organizations
        ],
        "ai_cost_eur": session.scalar(
            select(func.coalesce(func.sum(UsageRecord.estimated_cost_eur), 0))
        ),
        "manual_review": get_settings().email_require_approval,
        "email_provider": get_settings().email_provider,
    }


@router.get("/admin/deliveries/{delivery_id}")
def preview_delivery(
    delivery_id: uuid.UUID, identity: Annotated[object, Depends(require_admin)], session: DB
):
    row = session.get(Delivery, delivery_id)
    if not row or row.category in {"verify", "reset"}:
        raise HTTPException(404, "Digest not found")
    return {"subject": row.subject, "text": row.text_body, "status": row.status}


@router.post("/admin/deliveries/{delivery_id}/approve")
def approve_delivery(
    delivery_id: uuid.UUID, identity: Annotated[object, Depends(require_admin)], session: DB
):
    row = session.get(Delivery, delivery_id, with_for_update=True)
    if not row or row.status != "review":
        raise HTTPException(409, "Delivery is not awaiting review")
    row.status = "pending"
    audit(session, identity, "digest_approved", {"delivery_id": str(delivery_id)})
    session.commit()
    return {"message": "Approved for the configured delivery mode"}


@router.post("/admin/jobs/{job_id}/retry")
def retry_job(job_id: uuid.UUID, identity: Annotated[object, Depends(require_admin)], session: DB):
    row = session.get(Job, job_id, with_for_update=True)
    if not row or row.status != "failed":
        raise HTTPException(409, "Only failed jobs can be retried")
    row.status, row.attempts, row.available_at = "pending", 0, datetime.now(UTC)
    audit(session, identity, "job_retried", {"job_id": str(job_id)})
    session.commit()
    return {"message": "Job queued"}
