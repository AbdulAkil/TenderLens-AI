import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from tenderlens.config import get_settings
from tenderlens.database.session import get_session
from tenderlens.saas.models import (
    AuditEvent,
    AuthSession,
    Membership,
    Organization,
    RateBucket,
    User,
)

passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


@dataclass
class Identity:
    user: User
    organization: Organization
    role: str


def current_identity(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> Identity:
    token = request.cookies.get(get_settings().session_cookie, "")
    if not token:
        raise HTTPException(401, "Sign in to continue")
    auth = session.get(AuthSession, token_hash(token))
    if not auth or aware(auth.expires_at) <= datetime.now(UTC):
        raise HTTPException(401, "Your session expired. Sign in again.")
    membership = session.get(Membership, (auth.user_id, auth.organization_id))
    user = session.get(User, auth.user_id)
    organization = session.get(Organization, auth.organization_id)
    if not membership or not user or not organization or organization.deletion_requested_at:
        raise HTTPException(401, "Account is unavailable")
    if not user.verified:
        raise HTTPException(403, "Verify your email before signing in")
    return Identity(user, organization, membership.role)


IdentityDependency = Annotated[Identity, Depends(current_identity)]


def require_manager(identity: IdentityDependency) -> Identity:
    if identity.role not in {"owner", "admin"}:
        raise HTTPException(403, "Organization administrator permission required")
    return identity


def require_admin(identity: IdentityDependency) -> Identity:
    allowed = {
        email.strip().lower() for email in get_settings().admin_emails.split(",") if email.strip()
    }
    if identity.user.email not in allowed:
        raise HTTPException(403, "Internal administrator permission required")
    return identity


def audit(session: Session, identity: Identity, action: str, detail: dict | None = None) -> None:
    session.add(
        AuditEvent(
            organization_id=identity.organization.id,
            user_id=identity.user.id,
            action=action,
            detail=detail or {},
        )
    )


def rate_limit(session: Session, key: str, limit: int = 10, seconds: int = 900) -> None:
    """Database-shared fixed windows; ignore untrusted forwarding headers."""
    now = datetime.now(UTC)
    window = int(now.timestamp()) // seconds
    digest = token_hash(f"{key}:{window}")
    if session.bind.dialect.name == "postgresql":
        statement = insert(RateBucket).values(
            key=digest, count=1, expires_at=now + timedelta(seconds=seconds * 2)
        )
        count = session.scalar(
            statement.on_conflict_do_update(
                index_elements=[RateBucket.key], set_={"count": RateBucket.count + 1}
            ).returning(RateBucket.count)
        )
    else:
        bucket = session.get(RateBucket, digest)
        if bucket:
            bucket.count += 1
        else:
            bucket = RateBucket(
                key=digest, count=1, expires_at=now + timedelta(seconds=seconds * 2)
            )
            session.add(bucket)
        count = bucket.count
    session.commit()
    if count > limit:
        raise HTTPException(
            429, "Too many requests. Please try again later.", headers={"Retry-After": str(seconds)}
        )


def request_key(request: Request, purpose: str) -> str:
    return f"{purpose}:{request.client.host if request.client else 'unknown'}"
