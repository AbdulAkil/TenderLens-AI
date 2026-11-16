import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import select
from test_commercial import register
from test_matching_regressions import company

from tenderlens.config import get_settings
from tenderlens.ingestion.normalization import normalize_ted_notice
from tenderlens.ingestion.runner import TedIngestionRunner
from tenderlens.ingestion.ted_client import TedClient
from tenderlens.models.company import CompanyProfile
from tenderlens.ranking import matching
from tenderlens.ranking.matching import DeterministicMatcher
from tenderlens.repositories import companies
from tenderlens.saas import digest_state, worker
from tenderlens.saas.email import deliver_pending
from tenderlens.saas.models import Delivery, Organization
from tenderlens.schemas.ingestion import TedIngestionRequest

FIXTURE = json.loads(
    (
        Path(__file__).parents[2] / "evaluation/datasets/belgian-matching-review-20261115.json"
    ).read_text(encoding="utf-8")
)
AS_OF = datetime.fromisoformat(FIXTURE["as_of"])


class ReviewClock(datetime):
    @classmethod
    def now(cls, tz=UTC):
        return AS_OF.astimezone(tz)


@pytest.mark.parametrize("notice", FIXTURE["notices"], ids=lambda n: n["publication-number"])
def test_reviewed_belgian_opportunities(notice):
    normalized = normalize_ted_notice(notice)
    tender = SimpleNamespace(
        **{
            **normalized.__dict__,
            "documents": [],
            "country_code": normalized.buyer_country_code,
            "cpv_code_values": normalized.cpv_codes,
        }
    )
    active = normalized.status not in {"closed", "planning", "cancelled"} and (
        normalized.submission_deadline is None or normalized.submission_deadline > AS_OF
    )
    for service, positives in FIXTURE["positive_active_by_service"].items():
        score = DeterministicMatcher().score(company(services=[service]), tender).overall_score
        assert (active and score >= 40) == (normalized.source_id in positives), (service, score)


def test_real_projection_ingestion_to_reviewed_dry_run_email(db, monkeypatch):
    # Freeze the source review date rather than moving real deadlines into the future.
    for module in (matching, worker, digest_state, companies):
        monkeypatch.setattr(module, "datetime", ReviewClock)
    settings = get_settings()
    monkeypatch.setattr(settings, "email_provider", "dry_run")
    monkeypatch.setattr(settings, "email_require_approval", True)
    monkeypatch.setattr(settings, "admin_emails", "owner@example.com")
    client = register(db)
    org = db.scalar(select(Organization))
    profile = CompanyProfile(organization_id=org.id, name="Software SME", services=["software"])
    db.add(profile)
    db.commit()

    def ted_response(request):
        payload = json.loads(request.content)
        assert "notice-type" in payload["fields"]
        assert "deadline-receipt-request" in payload["fields"]
        return httpx.Response(200, json={"notices": FIXTURE["notices"], "totalNoticeCount": 15})

    async def ingest():
        async with httpx.AsyncClient(
            base_url="https://api.ted.europa.eu", transport=httpx.MockTransport(ted_response)
        ) as transport:
            return await TedIngestionRunner(db, TedClient(client=transport)).run(
                TedIngestionRequest(query=FIXTURE["query"], scope="ALL", max_notices=15)
            )

    first, second = asyncio.run(ingest()), asyncio.run(ingest())
    assert first.inserted == 15 and first.complete
    assert second.unchanged == 15 and second.updated == 0
    response = client.post(f"/api/v1/companies/{profile.id}/matches/recalculate")
    assert response.status_code == 201, response.text
    matches = response.json()["items"]
    assert [item["tender"]["source_id"] for item in matches] == ["757153-2026"]
    assert matches[0]["overall_score"] == 100
    assert worker.build_digests(db) == 1
    digest = db.scalar(select(Delivery).where(Delivery.category == "digest"))
    assert digest.status == "review" and "757153-2026" in digest.text_body
    assert "2026-12-03" in digest.text_body
    assert "published earlier" in digest.text_body
    assert client.get(f"/api/v1/admin/deliveries/{digest.id}").status_code == 200
    assert client.post(f"/api/v1/admin/deliveries/{digest.id}/approve").status_code == 200
    asyncio.run(deliver_pending(db))
    assert digest.status == "dry_run" and digest.provider_id is None
    assert worker.build_digests(db) == 0
