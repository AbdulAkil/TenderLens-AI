import asyncio
import base64
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from svix.webhooks import Webhook
from test_commercial import register

from tenderlens.config import get_settings
from tenderlens.main import app
from tenderlens.saas.models import Delivery, Job, Organization


def test_worker_retry_and_final_crash_recovery(db, monkeypatch):
    import tenderlens.saas.worker as worker

    monkeypatch.setattr(worker, "SessionLocal", sessionmaker(bind=db.bind))
    monkeypatch.setattr(worker, "schedule", lambda session: None)
    job = Job(kind="invalid", dedup_key="test-recovery")
    db.add(job)
    db.commit()
    asyncio.run(worker.tick())
    db.expire_all()
    assert job.status == "pending" and job.attempts == 1
    job.status = "running"
    job.attempts = 5
    job.lease_until = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    asyncio.run(worker.tick())
    db.expire_all()
    assert job.status == "failed"


def test_checkout_and_portal_use_owned_customer_and_server_prices(db, monkeypatch):
    import tenderlens.saas.billing as billing

    client = register(db)
    calls = []
    provider = SimpleNamespace(
        v1=SimpleNamespace(
            customers=SimpleNamespace(
                create=lambda params, options: SimpleNamespace(id="cus_test_owned")
            ),
            checkout=SimpleNamespace(
                sessions=SimpleNamespace(
                    create=lambda params, options: (
                        calls.append((params, options))
                        or SimpleNamespace(url="https://checkout.stripe.com/test")
                    )
                )
            ),
            billing_portal=SimpleNamespace(
                sessions=SimpleNamespace(
                    create=lambda params: SimpleNamespace(url="https://billing.stripe.com/test")
                )
            ),
        )
    )
    monkeypatch.setattr(billing, "stripe_client", lambda: provider)
    monkeypatch.setattr(get_settings(), "stripe_starter_price", "price_owned_config")
    response = client.post("/api/v1/billing/checkout", json={"plan": "starter"})
    assert response.status_code == 200
    params, options = calls[0]
    assert params["customer"] == "cus_test_owned"
    assert params["line_items"][0]["price"] == "price_owned_config"
    assert options["idempotency_key"].startswith("checkout:")
    assert client.post("/api/v1/billing/portal").status_code == 200
    org = db.scalar(select(Organization))
    org.stripe_subscription_id = "sub_current"
    org.subscription_status = "active"
    db.commit()
    assert client.post("/api/v1/billing/checkout", json={"plan": "starter"}).status_code == 409


def test_signed_bounce_suppresses_recipient_and_replay(db, monkeypatch):
    register(db)
    row = db.scalar(select(Delivery).where(Delivery.category == "welcome"))
    row.provider_id = "email_test"
    row.status = "sent"
    db.commit()
    secret = "whsec_" + base64.b64encode(b"test-webhook-secret-32-bytes-long!").decode()
    monkeypatch.setattr(get_settings(), "email_webhook_secret", secret)
    body = json.dumps({"type": "email.bounced", "data": {"email_id": "email_test"}})
    timestamp = datetime.now(UTC)
    signature = Webhook(secret).sign("msg_test", timestamp, body)
    headers = {
        "svix-id": "msg_test",
        "svix-timestamp": str(int(timestamp.timestamp())),
        "svix-signature": signature,
    }
    client = TestClient(app)
    assert client.post("/api/v1/email/webhook", content=body, headers=headers).status_code == 200
    assert row.status == "bounced"
    assert client.post("/api/v1/email/webhook", content=body, headers=headers).json()["duplicate"]
    assert (
        client.post(
            "/api/v1/email/webhook", content=body, headers={**headers, "svix-signature": "forged"}
        ).status_code
        == 400
    )


def test_anonymous_private_endpoints_remain_protected(db):
    client = TestClient(app)
    for path in [
        "/api/v1/companies",
        "/api/v1/auth/me",
        "/api/v1/admin/overview",
        "/api/v1/account/export",
        "/api/v1/notifications/history",
    ]:
        assert client.get(path).status_code == 401


def test_request_limit_precedes_json_parsing():
    assert TestClient(app).post("/api/v1/auth/signup", content=b"x" * 1_000_001).status_code == 413
