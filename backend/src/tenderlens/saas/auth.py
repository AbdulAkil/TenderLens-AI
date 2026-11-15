import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tenderlens.config import get_settings
from tenderlens.database.session import get_session
from tenderlens.saas.email import queue_email
from tenderlens.saas.models import (
    ActionToken,
    AuthSession,
    Membership,
    NotificationPreference,
    Organization,
    User,
)
from tenderlens.saas.security import (
    DUMMY_HASH,
    IdentityDependency,
    audit,
    aware,
    passwords,
    rate_limit,
    request_key,
    token_hash,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
DB = Annotated[Session, Depends(get_session)]


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class Signup(Credentials):
    organization_name: str = Field(min_length=2, max_length=256)
    accept_terms: bool


class EmailInput(BaseModel):
    email: EmailStr


class TokenInput(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class ResetInput(TokenInput):
    password: str = Field(min_length=12, max_length=128)


def issue_action(session: Session, user: User, purpose: str, organization_id=None) -> None:
    token = secrets.token_urlsafe(32)
    session.execute(
        delete(ActionToken).where(ActionToken.user_id == user.id, ActionToken.purpose == purpose)
    )
    session.add(
        ActionToken(
            token_hash=token_hash(token),
            user_id=user.id,
            purpose=purpose,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
    )
    url = f"{get_settings().site_url}/auth/{'verify' if purpose == 'verify' else 'reset'}#token={token}"
    subject = (
        "Verify your TenderLens email" if purpose == "verify" else "Reset your TenderLens password"
    )
    queue_email(
        session,
        user=user,
        organization_id=organization_id,
        key=f"{purpose}:{token_hash(token)}",
        category=purpose,
        subject=subject,
        text=f"{subject}. This link expires in 30 minutes.\n{url}\nIf you did not request this, ignore this email.",
        action_url=url,
        essential=True,
    )


@router.post("/signup", status_code=202)
def signup(payload: Signup, request: Request, session: DB):
    rate_limit(session, request_key(request, "signup"), 5)
    if not payload.accept_terms:
        raise HTTPException(422, "Accept the terms and privacy notice to create an account")
    email = str(payload.email).lower()
    if not session.scalar(select(User).where(User.email == email)):
        user = User(email=email, password_hash=passwords.hash(payload.password))
        organization = Organization(
            name=payload.organization_name,
            trial_ends_at=datetime.now(UTC) + timedelta(days=get_settings().trial_days),
        )
        session.add_all([user, organization])
        try:
            session.flush()
            session.add(Membership(user_id=user.id, organization_id=organization.id, role="owner"))
            session.add(NotificationPreference(user_id=user.id, organization_id=organization.id))
            issue_action(session, user, "verify", organization.id)
            session.commit()
        except IntegrityError:
            session.rollback()
    return {
        "message": "If this address can be registered, a verification email has been queued. In local dry-run mode, inspect it with the operator CLI."
    }


def consume_token(session: Session, token: str, purpose: str) -> User:
    action = session.scalar(
        select(ActionToken).where(ActionToken.token_hash == token_hash(token)).with_for_update()
    )
    if not action or action.purpose != purpose or aware(action.expires_at) <= datetime.now(UTC):
        raise HTTPException(400, "This link is invalid or expired. Request another email.")
    user = session.get(User, action.user_id)
    session.delete(action)
    return user


@router.post("/verify")
def verify(payload: TokenInput, request: Request, session: DB):
    rate_limit(session, request_key(request, "verify"), 20)
    user = consume_token(session, payload.token, "verify")
    user.verified = True
    session.commit()
    return {"message": "Email verified. You can sign in."}


@router.post("/login")
def login(payload: Credentials, request: Request, response: Response, session: DB):
    rate_limit(session, request_key(request, "login"), 20)
    rate_limit(session, f"login-email:{str(payload.email).lower()}", 10)
    user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
    valid = passwords.verify(payload.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Email or password is incorrect")
    if not user.verified:
        raise HTTPException(403, "Verify your email before signing in")
    membership = session.scalar(
        select(Membership)
        .join(Organization)
        .where(Membership.user_id == user.id, Organization.deletion_requested_at.is_(None))
        .order_by(Membership.organization_id)
    )
    if not membership:
        raise HTTPException(403, "No active organization membership")
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    old_token = request.cookies.get(settings.session_cookie)
    if old_token:
        session.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(old_token)))
    session.add(
        AuthSession(
            token_hash=token_hash(token),
            user_id=user.id,
            organization_id=membership.organization_id,
            expires_at=datetime.now(UTC) + timedelta(hours=settings.session_hours),
        )
    )
    session.commit()
    response.set_cookie(
        settings.session_cookie,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.production,
        samesite="lax",
        path="/",
    )
    return {"message": "Signed in"}


@router.post("/logout")
def logout(request: Request, response: Response, session: DB):
    token = request.cookies.get(get_settings().session_cookie, "")
    session.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(token)))
    session.commit()
    response.delete_cookie(get_settings().session_cookie, path="/")
    return {"message": "Signed out"}


@router.get("/me")
def me(identity: IdentityDependency):
    org = identity.organization
    return {
        "email": identity.user.email,
        "user_id": str(identity.user.id),
        "organization_id": str(org.id),
        "organization_name": org.name,
        "role": identity.role,
        "plan": org.plan,
        "subscription_status": org.subscription_status,
        "trial_ends_at": org.trial_ends_at,
        "is_admin": identity.user.email
        in {e.strip().lower() for e in get_settings().admin_emails.split(",") if e.strip()},
    }


@router.post("/forgot-password", status_code=202)
def forgot(payload: EmailInput, request: Request, session: DB):
    rate_limit(session, request_key(request, "forgot"), 5)
    user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user:
        issue_action(session, user, "reset")
        session.commit()
    return {"message": "If the account exists, a reset email has been queued."}


@router.post("/resend-verification", status_code=202)
def resend(payload: EmailInput, request: Request, session: DB):
    rate_limit(session, request_key(request, "resend"), 5)
    user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user and not user.verified:
        issue_action(session, user, "verify")
        session.commit()
    return {"message": "If verification is needed, a new email has been queued."}


@router.post("/reset-password")
def reset(payload: ResetInput, request: Request, session: DB):
    rate_limit(session, request_key(request, "reset"), 10)
    user = consume_token(session, payload.token, "reset")
    user.password_hash = passwords.hash(payload.password)
    session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    session.commit()
    return {"message": "Password updated. Sign in with your new password."}


class DeleteInput(BaseModel):
    password: str = Field(max_length=128)


@router.post("/deletion-request", status_code=202)
def request_deletion(payload: DeleteInput, identity: IdentityDependency, session: DB):
    if identity.role != "owner" or not passwords.verify(
        payload.password, identity.user.password_hash
    ):
        raise HTTPException(403, "Organization owner and correct password required")
    identity.organization.deletion_requested_at = datetime.now(UTC)
    session.execute(
        delete(AuthSession).where(AuthSession.organization_id == identity.organization.id)
    )
    audit(session, identity, "deletion_requested")
    session.commit()
    return {
        "message": "Access revoked. Organization deletion requested; the operator must resolve billing/retention and complete erasure."
    }
