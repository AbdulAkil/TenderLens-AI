import asyncio
import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from tenderlens.config import get_settings
from tenderlens.main import app
from tenderlens.models.tender import Tender
from tenderlens.saas.billing import sync_subscription
from tenderlens.saas.email import deliver_pending, render_email, safe_link
from tenderlens.saas.models import AuthSession, Delivery, Organization, User
from tenderlens.saas.worker import build_digests, schedule

ORIGIN = {"Origin": "http://localhost:3000"}


def register(db, email="owner@example.com", company="Test consultancy"):
    client = TestClient(app, headers=ORIGIN)
    payload = {
        "email": email,
        "password": "Long test password 497!",
        "organization_name": company,
        "accept_terms": True,
    }
    assert client.post("/api/v1/auth/signup", json=payload).status_code == 202
    user = db.scalar(select(User).where(User.email == email))
    delivery = db.scalar(
        select(Delivery)
        .where(Delivery.user_id == user.id, Delivery.category == "verify")
        .order_by(Delivery.created_at.desc())
    )
    token = re.search(r"#token=([\w-]+)", delivery.text_body)[1]
    assert client.post("/api/v1/auth/verify", json={"token": token}).status_code == 200
    assert client.post("/api/v1/auth/verify", json={"token": token}).status_code == 400
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    return client


def test_signup_verification_login_reset_and_logout(db):
    client = register(db)
    assert client.get("/api/v1/auth/me").json()["role"] == "owner"
    assert db.scalar(select(AuthSession)).token_hash != client.cookies.get("tenderlens_session")
    assert (
        client.post("/api/v1/auth/forgot-password", json={"email": "owner@example.com"}).status_code
        == 202
    )
    reset = db.scalar(select(Delivery).where(Delivery.category == "reset"))
    token = re.search(r"#token=([\w-]+)", reset.text_body)[1]
    assert (
        client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "password": "Another test password 912!"},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/auth/me").status_code == 401


def test_cross_tenant_profile_saved_feedback_and_matches_denied(db):
    a = register(db)
    company = a.post("/api/v1/companies", json={"name": "Private A"}).json()
    b = register(db, "second@example.com", "Second organization")
    assert b.get("/api/v1/companies").json() == []
    company_id = company["id"]
    for path in [
        f"/companies/{company_id}",
        f"/companies/{company_id}/saved",
        f"/companies/{company_id}/matches",
    ]:
        assert b.get(f"/api/v1{path}").status_code == 404
    assert b.put(f"/api/v1/companies/{company_id}", json={"name": "Stolen"}).status_code == 404
    assert b.post(f"/api/v1/companies/{company_id}/matches/recalculate").status_code == 404
    assert (
        b.put(
            f"/api/v1/companies/{company_id}/feedback/{uuid.uuid4()}", json={"value": "relevant"}
        ).status_code
        == 404
    )
    assert b.delete(f"/api/v1/companies/{company_id}/saved/{uuid.uuid4()}").status_code == 404
    assert b.get("/api/v1/admin/overview").status_code == 403
    assert len(a.get("/api/v1/companies").json()) == 1


def test_full_customer_digest_workflow_is_idempotent_and_opt_out_respected(db):
    client = register(db)
    result = client.post(
        "/api/v1/companies",
        json={
            "name": "Security SME",
            "description": "cybersecurity software development",
            "services": ["software", "cybersecurity"],
            "skills": ["Python"],
            "preferred_locations": ["BEL"],
        },
    )
    company_id = result.json()["id"]
    tender = Tender(
        source="ted",
        source_id="fixture-example",
        source_url="https://ted.europa.eu/en/notice/-/detail/fixture",
        title="Cybersecurity software Python development",
        description="Software delivery",
        country_code="BEL",
        raw_metadata={"test_fixture": True},
        ingested_at=datetime.now(UTC),
        submission_deadline=datetime.now(UTC) + timedelta(days=10),
    )
    db.add(tender)
    db.commit()
    response = client.post(f"/api/v1/companies/{company_id}/matches/recalculate")
    assert response.status_code == 201, response.text
    assert len(response.json()["items"]) == 1
    assert build_digests(db) == 1
    assert build_digests(db) == 0
    digest = db.scalar(select(Delivery).where(Delivery.category == "digest"))
    assert digest.status == "review"
    assert "Not disclosed" in digest.text_body
    assert "experimental" in digest.text_body
    digest.status = "pending"
    db.commit()
    asyncio.run(deliver_pending(db))
    assert digest.status == "dry_run"
    assert (
        client.post(
            f"/api/v1/tenders/{tender.id}/save", json={"company_id": company_id}
        ).status_code
        == 201
    )
    assert len(client.get(f"/api/v1/companies/{company_id}/saved").json()) == 1
    assert (
        client.put("/api/v1/notifications/preferences", json={"frequency": "off"}).status_code
        == 200
    )
    assert client.get("/api/v1/account/export").json()["saved"][0]["tender_id"] == str(tender.id)


def test_quotas_trial_expiry_and_csrf(db):
    client = register(db)
    assert client.post("/api/v1/companies", json={"name": "One"}).status_code == 201
    assert client.post("/api/v1/companies", json={"name": "Two"}).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/logout", headers={"Origin": "https://attacker.invalid"}
        ).status_code
        == 403
    )
    org = db.scalar(select(Organization))
    org.trial_ends_at = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    assert client.post("/api/v1/companies", json={"name": "Three"}).status_code == 402
    assert client.get("/api/v1/account/export").status_code == 200


def test_scheduler_deduplicates_and_forged_webhooks_fail(db, monkeypatch):
    schedule(db)
    schedule(db)
    from tenderlens.saas.models import Job

    assert db.scalar(select(func.count()).select_from(Job)) == 6
    monkeypatch.setattr(get_settings(), "stripe_webhook_secret", "whsec_test")
    assert (
        TestClient(app)
        .post("/api/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "forged"})
        .status_code
        == 400
    )


def test_subscription_sync_checks_ownership_and_status(db, monkeypatch):
    register(db)
    org = db.scalar(select(Organization))
    org.stripe_customer_id = "cus_test"
    monkeypatch.setattr(get_settings(), "stripe_starter_price", "price_test")
    sub = {
        "id": "sub_test",
        "customer": "cus_test",
        "metadata": {"organization_id": str(org.id)},
        "status": "active",
        "items": {"data": [{"price": {"id": "price_test"}}]},
    }
    sync_subscription(db, {"created": 100}, sub)
    db.commit()
    assert org.plan == "starter"
    assert org.subscription_status == "active"
    sub["status"] = "canceled"
    sync_subscription(db, {"created": 90}, sub)
    db.commit()
    assert org.subscription_status == "canceled"
    sub["customer"] = "cus_other"
    with pytest.raises(Exception, match="ownership"):
        sync_subscription(db, {}, sub)


def test_email_html_and_source_urls_are_safe():
    assert "<script>" not in render_email(
        "<script>alert(1)</script>", '<img src=x onerror="alert(1)">'
    )
    assert safe_link("javascript:alert(1)") is None
    assert safe_link("https://ted.europa.eu.attacker.com/a") is None
    assert safe_link("https://user:pass@ted.europa.eu/a") is None


def test_signup_rate_limit_is_shared_by_database(db):
    client = TestClient(app)
    payload = {
        "email": "rate@example.com",
        "password": "A valid long password!",
        "organization_name": "Rate",
        "accept_terms": True,
    }
    for _ in range(5):
        assert client.post("/api/v1/auth/signup", json=payload).status_code == 202
    assert (
        TestClient(app)
        .post("/api/v1/auth/signup", json=payload, headers={"X-Forwarded-For": "different"})
        .status_code
        == 429
    )
