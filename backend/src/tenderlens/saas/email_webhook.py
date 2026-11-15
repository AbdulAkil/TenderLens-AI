from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from tenderlens.config import get_settings
from tenderlens.database.session import get_session
from tenderlens.saas.models import BillingEvent, Delivery

router = APIRouter(prefix="/email", tags=["email delivery"])


@router.post("/webhook")
async def email_webhook(request: Request, session: Annotated[Session, Depends(get_session)]):
    secret = get_settings().email_webhook_secret
    if not secret:
        raise HTTPException(503, "Email webhook is not configured")
    payload = await request.body()
    if len(payload) > 1_000_000:
        raise HTTPException(413, "Payload too large")
    try:
        event = Webhook(secret).verify(payload, dict(request.headers))
    except (WebhookVerificationError, ValueError):
        raise HTTPException(400, "Invalid email webhook signature") from None
    event_id = f"email:{request.headers['svix-id']}"
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy import text

        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": event_id})
    if session.get(BillingEvent, event_id):
        return {"received": True, "duplicate": True}
    event_type = event.get("type", "unknown")
    row = session.scalar(
        select(Delivery).where(Delivery.provider_id == event.get("data", {}).get("email_id"))
    )
    if not row and event_type in {"email.bounced", "email.complained", "email.delivered"}:
        # Provider callbacks can beat the outbox commit. Retry rather than lose it.
        raise HTTPException(503, "Delivery record not committed yet; retry this event")
    if row:
        if event_type in {"email.bounced", "email.complained"}:
            row.status = "bounced" if event_type == "email.bounced" else "complained"
        elif event_type == "email.delivered" and row.status not in {"bounced", "complained"}:
            row.status = "delivered"
    session.add(BillingEvent(id=event_id, event_type=event_type))
    session.commit()
    return {"received": True}
