import time
import uuid
from typing import Annotated, Literal

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tenderlens.config import get_settings
from tenderlens.database.session import get_session
from tenderlens.saas.models import BillingEvent, Organization
from tenderlens.saas.plans import plans
from tenderlens.saas.security import IdentityDependency, audit, require_manager

router = APIRouter(prefix="/billing", tags=["billing"])
DB = Annotated[Session, Depends(get_session)]


def stripe_client():
    key = get_settings().stripe_secret_key or ""
    if not key.startswith("sk_test_"):
        raise HTTPException(
            503, "Billing requires a Stripe test-mode key. Live payments are disabled."
        )
    return stripe.StripeClient(key)


@router.get("/plans")
def get_plans():
    return {key: value.model_dump() for key, value in plans().items()}


class CheckoutInput(BaseModel):
    plan: Literal["starter", "professional", "business"]


@router.post("/checkout")
def checkout(payload: CheckoutInput, identity: IdentityDependency, session: DB):
    require_manager(identity)
    client = stripe_client()
    settings = get_settings()
    price = getattr(settings, f"stripe_{payload.plan}_price")
    if not price:
        raise HTTPException(503, "Configure the test-mode Stripe price for this plan")
    session.refresh(identity.organization, with_for_update=True)
    org = identity.organization
    if org.stripe_subscription_id and org.subscription_status != "canceled":
        raise HTTPException(
            409, "Use the billing portal to change or cancel your existing subscription"
        )
    if not org.stripe_customer_id:
        customer = client.v1.customers.create(
            {
                "email": identity.user.email,
                "name": org.name,
                "metadata": {"organization_id": str(org.id)},
            },
            options={"idempotency_key": f"customer:{org.id}"},
        )
        org.stripe_customer_id = customer.id
        session.commit()
    # No trial in Checkout: the application trial was already granted at signup.
    result = client.v1.checkout.sessions.create(
        {
            "mode": "subscription",
            "customer": org.stripe_customer_id,
            "line_items": [{"price": price, "quantity": 1}],
            "client_reference_id": str(org.id),
            "subscription_data": {"metadata": {"organization_id": str(org.id)}},
            "tax_id_collection": {"enabled": True},
            "billing_address_collection": "required",
            "success_url": f"{settings.site_url}/billing?checkout=returned",
            "cancel_url": f"{settings.site_url}/billing",
        },
        options={"idempotency_key": f"checkout:{org.id}:{payload.plan}:{int(time.time()) // 1800}"},
    )
    audit(session, identity, "checkout_created", {"plan": payload.plan})
    session.commit()
    return {"url": result.url}


@router.post("/portal")
def portal(identity: IdentityDependency):
    require_manager(identity)
    if not identity.organization.stripe_customer_id:
        raise HTTPException(409, "Create a test checkout first")
    result = stripe_client().v1.billing_portal.sessions.create(
        {
            "customer": identity.organization.stripe_customer_id,
            "return_url": f"{get_settings().site_url}/billing",
        }
    )
    return {"url": result.url}


@router.get("/invoices")
def invoices(identity: IdentityDependency):
    require_manager(identity)
    if not identity.organization.stripe_customer_id:
        return []
    rows = stripe_client().v1.invoices.list(
        {"customer": identity.organization.stripe_customer_id, "limit": 24}
    )
    return [
        {
            "id": row.id,
            "status": row.status,
            "amount_paid": row.amount_paid,
            "currency": row.currency,
            "url": row.hosted_invoice_url,
        }
        for row in rows.data
    ]


def sync_subscription(session: Session, event: dict, subscription: dict) -> None:
    """Use provider-fetched current state; metadata can never come from a browser."""
    metadata = subscription.get("metadata") or {}
    try:
        org_id = uuid.UUID(metadata.get("organization_id", ""))
    except (ValueError, TypeError):
        raise HTTPException(400, "Subscription has no recognized organization") from None
    org = session.get(Organization, org_id, with_for_update=True)
    if not org or org.stripe_customer_id != subscription.get("customer"):
        raise HTTPException(400, "Subscription/customer ownership mismatch")
    if (
        org.stripe_subscription_id
        and org.stripe_subscription_id != subscription["id"]
        and org.subscription_status in {"active", "trialing", "past_due"}
    ):
        # A delayed event for a previous subscription must not revoke its replacement.
        return
    items = subscription.get("items", {}).get("data", [])
    price_ids = {item.get("price", {}).get("id") for item in items}
    mapped = {
        getattr(get_settings(), f"stripe_{name}_price"): name
        for name in plans()
        if getattr(get_settings(), f"stripe_{name}_price", "")
    }
    plan = next((mapped[p] for p in price_ids if p in mapped), None)
    if not plan:
        raise HTTPException(400, "Unrecognized subscription price; no entitlements granted")
    org.plan = plan
    org.subscription_status = subscription["status"]
    org.stripe_subscription_id = subscription["id"]
    org.billing_event_created = max(org.billing_event_created, int(event.get("created", 0)))


@router.post("/webhook")
async def webhook(request: Request, session: DB):
    secret = get_settings().stripe_webhook_secret
    if not secret:
        raise HTTPException(503, "Stripe webhook signing secret is not configured")
    body = await request.body()
    if len(body) > 1_000_000:
        raise HTTPException(413, "Webhook payload too large")
    try:
        event = stripe.Webhook.construct_event(
            body, request.headers.get("stripe-signature", ""), secret
        ).to_dict()
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook signature") from None
    if event.get("livemode"):
        raise HTTPException(400, "Live billing events are disabled")
    # Serialize concurrent duplicate event deliveries before checking the event log.
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy import text

        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": event["id"]})
    if session.get(BillingEvent, event["id"]):
        return {"received": True, "duplicate": True}
    event_type = event["type"]
    obj = event["data"]["object"]
    subscription_id = (
        obj.get("id")
        if event_type.startswith("customer.subscription.")
        else obj.get("subscription")
    )
    if not subscription_id and event_type.startswith("invoice."):
        subscription_id = (
            (obj.get("parent") or {}).get("subscription_details", {}).get("subscription")
        )
    if subscription_id and (
        event_type.startswith("customer.subscription.")
        or event_type in {"invoice.paid", "invoice.payment_failed", "checkout.session.completed"}
    ):
        # Refetch to avoid stale/out-of-order webhooks restoring canceled access.
        current = stripe_client().v1.subscriptions.retrieve(subscription_id)
        sync_subscription(session, event, current.to_dict())
    session.add(BillingEvent(id=event["id"], event_type=event_type))
    session.commit()
    return {"received": True}
