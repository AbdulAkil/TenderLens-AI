"""Transactional outbox. Defaults to dry run; live recipients remain disallowed."""

import html
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from tenderlens.config import get_settings
from tenderlens.saas.models import Delivery, User


def safe_link(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443):
        return None
    if parts.hostname not in {"ted.europa.eu", "www.publicprocurement.be", "publicprocurement.be"}:
        return None
    return url


def render_email(title: str, text: str, action_url: str | None = None) -> str:
    escaped = html.escape(text).replace("\n", "<br>")
    action = (
        f'<p><a href="{html.escape(action_url, quote=True)}">Open TenderLens</a></p>'
        if action_url
        else ""
    )
    return f"""<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;background:#f3f5f2;font-family:Arial,sans-serif;color:#172e29">
<table role="presentation" width="100%"><tr><td style="padding:24px 12px"><table role="presentation" width="100%" style="max-width:600px;margin:auto;background:white"><tr><td style="padding:28px">
<p style="font-weight:bold">TenderLens AI</p><h1 style="font-size:24px">{html.escape(title)}</h1><p style="line-height:1.7">{escaped}</p>{action}
<p style="font-size:12px">Source evidence supports your decision. Always verify the official notice before bidding.</p></td></tr></table></td></tr></table></body></html>"""


def queue_email(
    session: Session,
    *,
    user: User,
    organization_id,
    key: str,
    category: str,
    subject: str,
    text: str,
    action_url: str | None = None,
    essential: bool = False,
) -> Delivery:
    existing = session.scalar(select(Delivery).where(Delivery.dedup_key == key))
    if existing:
        return existing
    review = get_settings().email_require_approval and not essential
    delivery = Delivery(
        user_id=user.id,
        organization_id=organization_id,
        dedup_key=key,
        category=category,
        recipient=user.email,
        subject=subject,
        text_body=text,
        html_body=render_email(subject, text, action_url),
        status="review" if review else "pending",
    )
    session.add(delivery)
    session.flush()
    return delivery


async def deliver_pending(session: Session) -> int:
    settings = get_settings()
    rows = session.scalars(
        select(Delivery)
        .where(Delivery.status == "pending", Delivery.available_at <= datetime.now(UTC))
        .order_by(Delivery.created_at)
        .limit(25)
        .with_for_update(skip_locked=True)
    ).all()
    sent = 0
    for row in rows:
        try:
            suppressed = session.scalar(
                select(Delivery.id)
                .where(
                    Delivery.recipient == row.recipient,
                    Delivery.status.in_(["bounced", "complained"]),
                )
                .limit(1)
            )
            if suppressed:
                row.status = "suppressed"
                session.commit()
                continue
            from tenderlens.saas.models import Membership, NotificationPreference, Organization

            if row.category not in {"verify", "reset", "welcome", "billing"}:
                pref = session.get(NotificationPreference, (row.user_id, row.organization_id))
                org = session.get(Organization, row.organization_id)
                member = session.get(Membership, (row.user_id, row.organization_id))
                user = session.get(User, row.user_id)
                if (
                    not pref
                    or pref.frequency == "off"
                    or not org
                    or org.deletion_requested_at
                    or not member
                    or not user
                    or not user.verified
                    or (row.category == "deadline" and not pref.deadline_reminders)
                    or (row.category in {"update", "cancellation"} and not pref.updates)
                ):
                    row.status = "suppressed"
                    session.commit()
                    continue
                from fastapi import HTTPException

                from tenderlens.saas.plans import entitlement

                try:
                    entitlement(org)
                except HTTPException:
                    row.status = "suppressed"
                    session.commit()
                    continue
            if settings.email_provider == "dry_run":
                row.status = "dry_run"
            elif settings.email_provider == "resend":
                allowed = {
                    email.strip().lower()
                    for email in settings.email_sandbox_recipients.split(",")
                    if email.strip()
                }
                if not settings.email_api_key or row.recipient.lower() not in allowed:
                    raise ValueError(
                        "Recipient is not an authorized sandbox recipient or provider key is absent"
                    )
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": f"Bearer {settings.email_api_key}",
                            "Idempotency-Key": str(row.id),
                        },
                        json={
                            "from": settings.email_from,
                            "to": [row.recipient],
                            "subject": row.subject,
                            "text": row.text_body,
                            "html": row.html_body,
                        },
                    )
                    response.raise_for_status()
                    row.provider_id = response.json()["id"]
                row.status = "sent"
            else:
                raise ValueError("Unsupported email provider")
            row.last_error = None
            sent += 1
        except (httpx.HTTPError, ValueError, KeyError):
            row.attempts += 1
            row.status = "failed" if row.attempts >= 5 else "pending"
            row.available_at = datetime.now(UTC) + timedelta(minutes=2**row.attempts)
            row.last_error = "Delivery failed; check provider configuration and sandbox allowlist"
        session.commit()
    return sent
