import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select, text
from test_commercial import register

from tenderlens.models.company import CompanyProfile, TenderMatch
from tenderlens.models.matching import DigestOpportunity, MatchEvaluation
from tenderlens.models.tender import Tender
from tenderlens.ranking.matching import DeterministicMatcher, MatchService
from tenderlens.repositories.companies import CompanyRepository
from tenderlens.saas.email import deliver_pending
from tenderlens.saas.models import (
    Delivery,
    Job,
    NotificationPreference,
    Organization,
    TenderFeedback,
)
from tenderlens.saas.worker import build_digests, execute_job


def company(**changes):
    return SimpleNamespace(
        description=None,
        services=changes.pop("services", ["software development"]),
        industries=[],
        skills=changes.pop("skills", []),
        preferred_locations=changes.pop("preferred_locations", []),
        certifications=[],
        cpv_codes=changes.pop("cpv_codes", []),
        minimum_contract_value=changes.pop("minimum_contract_value", None),
        maximum_contract_value=changes.pop("maximum_contract_value", None),
        **changes,
    )


def tender(**changes):
    return SimpleNamespace(
        title=changes.pop("title", "Software development"),
        description=None,
        documents=[],
        country_code=changes.pop("country_code", None),
        estimated_value=changes.pop("estimated_value", None),
        currency=changes.pop("currency", None),
        cpv_code_values=changes.pop("cpv_code_values", []),
        **changes,
    )


def setup_profile(db):
    register(db)
    org = db.scalar(select(Organization))
    profile = CompanyProfile(
        organization_id=org.id, name="Services-only SME", services=["software development"]
    )
    db.add(profile)
    db.commit()
    return profile


def add_notice(db, index, **changes):
    notice = Tender(
        source="test",
        source_id=str(index),
        source_url=f"https://ted.europa.eu/en/notice/-/detail/{index}",
        title=changes.pop("title", "Software development"),
        raw_metadata={"fixture": True},
        ingested_at=changes.pop("ingested_at", datetime.now(UTC)),
        submission_deadline=changes.pop(
            "submission_deadline", datetime.now(UTC) + timedelta(days=30)
        ),
        **changes,
    )
    db.add(notice)
    return notice


def test_services_only_perfect_match_crosses_default_notification_threshold():
    result = DeterministicMatcher().score(company(), tender())
    assert result.overall_score == 100
    assert result.component_scores["skills"] is None
    assert result.component_scores["location"] is None
    assert result.component_scores["eligibility"] is None
    assert not any("outside" in blocker or "differs" in blocker for blocker in result.blockers)


def test_known_negative_evidence_is_not_treated_as_missing():
    matcher = DeterministicMatcher()
    unknown = matcher.score(company(skills=["Python"]), tender())
    positive = matcher.score(
        company(skills=["Python"]), tender(title="Software development in Python")
    )
    assert unknown.component_scores["skills"] == 0
    assert positive.component_scores["skills"] == 1
    assert unknown.overall_score < positive.overall_score
    assert matcher.score(company(), tender(title="Road construction")).overall_score == 0
    assert (
        matcher.score(
            company(services=[], preferred_locations=["BEL"]), tender(country_code="BEL")
        ).overall_score
        == 0
    )


def test_missing_tender_cpv_is_unknown_and_broad_cpv_matches_descendants():
    matcher = DeterministicMatcher()
    assert matcher.score(company(cpv_codes=["72000000"]), tender()).component_scores["cpv"] is None
    assert (
        matcher.score(
            company(cpv_codes=["72000000"]), tender(cpv_code_values=["72210000"])
        ).component_scores["cpv"]
        == 1
    )
    assert (
        matcher.score(
            company(preferred_locations=["BEL"]), tender(country_code="FRA")
        ).overall_score
        > 40
    )


def test_complete_corpus_exceeds_1000_and_unchanged_recalculation_does_no_work(db):
    profile = setup_profile(db)
    old = add_notice(db, "old", ingested_at=datetime.now(UTC) - timedelta(days=300))
    for index in range(1005):
        add_notice(db, index)
    db.commit()
    service = MatchService(db)
    service.calculate_for_company(profile.id, batch_size=127)
    assert db.scalar(select(func.count()).select_from(TenderMatch)) == 1006
    assert db.scalar(select(TenderMatch.id).where(TenderMatch.tender_id == old.id))
    assert (
        len(CompanyRepository(db, profile.organization_id).list_matches(profile.id, limit=10)) == 10
    )
    assert service.process_batch(profile.id).processed == 0
    old.title = "Software development Python"
    db.commit()
    assert service.process_batch(profile.id).processed == 1


def test_partial_batches_preserve_matches_and_resume_after_interruption(db):
    profile = setup_profile(db)
    first = add_notice(db, "first")
    db.commit()
    MatchService(db).calculate_for_company(profile.id)
    for index in range(7):
        add_notice(db, index)
    db.commit()
    assert MatchService(db).process_batch(profile.id, batch_size=2).pending
    assert db.scalar(select(TenderMatch.id).where(TenderMatch.tender_id == first.id))
    assert build_digests(db) == 0
    # A new service instance resumes from persisted evaluations, not an in-memory cursor.
    MatchService(db).calculate_for_company(profile.id, batch_size=2)
    assert db.scalar(select(func.count()).select_from(TenderMatch)) == 8
    assert build_digests(db) == 1


def test_profile_change_rechecks_rejections_and_expiry_prunes_only_inactive(db):
    profile = setup_profile(db)
    add_notice(db, "useful")
    rejected = add_notice(db, "rejected", title="Electrical installation")
    db.commit()
    service = MatchService(db)
    service.calculate_for_company(profile.id)
    assert db.scalar(select(func.count()).select_from(MatchEvaluation)) == 2
    profile.services = ["electrical installation"]
    db.commit()
    assert CompanyRepository(db, profile.organization_id).list_matches(profile.id) == []
    service.calculate_for_company(profile.id)
    assert db.scalar(select(TenderMatch.tender_id)) == rejected.id
    rejected.submission_deadline = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    service.process_batch(profile.id)
    assert db.scalar(select(func.count()).select_from(TenderMatch)) == 0


def test_old_ingestion_is_new_for_recipient_and_not_repeated_next_period(db, monkeypatch):
    profile = setup_profile(db)
    notice = add_notice(db, "historical", ingested_at=datetime.now(UTC) - timedelta(days=100))
    db.commit()
    MatchService(db).calculate_for_company(profile.id)
    assert build_digests(db) == 1
    digest = db.scalar(select(Delivery).where(Delivery.category == "digest"))
    assert "published earlier" in digest.text_body
    digest.status = "pending"
    db.commit()
    asyncio.run(deliver_pending(db))
    assert digest.status == "dry_run"
    # Removing a delivery log never resets the durable recipient assignment.
    db.delete(digest)
    db.commit()
    assert build_digests(db) == 0
    assert db.scalar(select(func.count()).select_from(DigestOpportunity)) == 1
    notice.title = "Updated software development"
    db.commit()
    MatchService(db).calculate_for_company(profile.id)
    assert build_digests(db) == 0


def test_top_ten_overflow_is_retained_for_next_period(db):
    profile = setup_profile(db)
    for index in range(12):
        add_notice(db, index)
    db.commit()
    MatchService(db).calculate_for_company(profile.id)
    assert build_digests(db) == 1
    assert db.scalar(select(func.count()).select_from(DigestOpportunity)) == 10
    # Simulate the next period without advancing source deadlines or altering notices.
    digest = db.scalar(select(Delivery).where(Delivery.category == "digest"))
    digest.dedup_key += ":prior-period"
    digest.status = "dry_run"
    db.commit()
    assert build_digests(db) == 1
    assert db.scalar(select(func.count()).select_from(DigestOpportunity)) == 12


@pytest.mark.parametrize(
    "change",
    ["cancelled", "expired", "profile", "source", "deleted_profile", "feedback", "threshold"],
)
def test_stale_reviewed_digest_cannot_be_sent(db, change):
    profile = setup_profile(db)
    notice = add_notice(db, "draft")
    db.commit()
    MatchService(db).calculate_for_company(profile.id)
    assert build_digests(db) == 1
    digest = db.scalar(select(Delivery).where(Delivery.category == "digest"))
    digest.status = "pending"
    if change == "cancelled":
        notice.status = "cancelled"
    elif change == "expired":
        notice.submission_deadline = datetime.now(UTC) - timedelta(seconds=1)
    elif change == "profile":
        profile.services = ["construction"]
    elif change == "deleted_profile":
        db.delete(profile)
    elif change == "feedback":
        db.add(TenderFeedback(company_id=profile.id, tender_id=notice.id, value="irrelevant"))
    elif change == "threshold":
        # A current match can still fall below a newly raised recipient threshold.
        match = db.scalar(select(TenderMatch))
        match.overall_score = 60
        db.scalar(select(NotificationPreference)).minimum_score = 80
    else:
        notice.title = "Revised software development"
    db.commit()
    asyncio.run(deliver_pending(db))
    assert digest.status == "stale"
    assert db.scalar(select(func.count()).select_from(DigestOpportunity)) == 0


def test_tender_version_detects_changes_even_with_identical_timestamps(db):
    profile = setup_profile(db)
    notice = add_notice(db, "same-timestamp")
    db.commit()
    service = MatchService(db)
    service.calculate_for_company(profile.id)
    timestamp, version = notice.updated_at, notice.match_version
    notice.title = "Software development updated"
    notice.updated_at = timestamp
    db.commit()
    assert notice.match_version > version
    assert service.has_pending(profile)
    assert service.process_batch(profile.id).processed == 1


def test_generic_equipment_word_cannot_match_medical_supplier():
    assert (
        DeterministicMatcher()
        .score(company(services=["medical equipment"]), tender(title="Studio broadcast equipment"))
        .overall_score
        == 0
    )


def test_english_pronoun_is_not_it_capability_evidence():
    matcher = DeterministicMatcher()
    assert (
        matcher.score(
            company(services=["software"]), tender(title="Market research it commissions")
        ).overall_score
        == 0
    )
    assert matcher.score(company(services=["IT"]), tender(title="IT services")).overall_score == 100


def test_worker_continuations_finish_corpus_and_retry_without_reprocessing(db):
    profile = setup_profile(db)
    for index in range(401):
        add_notice(db, index)
    job = Job(
        kind="match_company", dedup_key="worker-test", payload={"company_id": str(profile.id)}
    )
    db.add(job)
    db.commit()
    result = asyncio.run(execute_job(job, db))
    assert result == {"processed": 200, "pending": True}
    continuation = db.scalar(select(Job).where(Job.id != job.id, Job.kind == "match_company"))
    assert asyncio.run(execute_job(continuation, db)) == {"processed": 200, "pending": True}
    # A retried parent can finish remaining work; persisted continuations are harmless.
    assert asyncio.run(execute_job(job, db)) == {"processed": 1, "pending": False}
    assert asyncio.run(execute_job(continuation, db)) == {"processed": 0, "pending": False}
    assert db.scalar(select(func.count()).select_from(TenderMatch)) == 401
    assert db.scalar(select(Job).where(Job.kind == "digest"))


def test_postgres_migration_preserves_history_and_closes_legacy_awards(db):
    if db.bind.dialect.name != "postgresql":
        pytest.skip("PostgreSQL migration/backfill semantics")
    import importlib.util
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    profile = setup_profile(db)
    notice = add_notice(db, "legacy-award")
    notice.source = "ted"
    notice.raw_metadata = {"notice-type": "can-standard"}
    db.commit()
    user_id = db.scalar(select(NotificationPreference.user_id))
    delivery = Delivery(
        user_id=user_id,
        organization_id=profile.organization_id,
        dedup_key="legacy-digest",
        category="digest",
        recipient="owner@example.com",
        subject="Historical digest",
        text_body=f"Workspace: http://localhost:3000/tenders/{notice.id}",
        html_body="",
        status="sent",
    )
    db.add(delivery)
    db.commit()
    notice_id, delivery_id = notice.id, delivery.id
    # Reconstruct exactly the tables/columns changed by 0009, in this test's
    # disposable schema, then exercise the actual migration against retained data.
    for statement in [
        "DROP TABLE digest_opportunities",
        "DROP TABLE match_evaluations",
        "DROP INDEX ix_tenders_matching_updated",
        "ALTER TABLE tenders DROP COLUMN match_version",
    ]:
        db.execute(text(statement))
    path = Path(__file__).parents[1] / "alembic/versions/20261115_0009_matching_delivery.py"
    spec = importlib.util.spec_from_file_location("matching_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with Operations.context(MigrationContext.configure(db.connection())):
        migration.upgrade()
    db.commit()
    db.expire_all()
    assert db.get(Tender, notice_id).status == "closed"
    receipt = db.scalar(select(DigestOpportunity))
    assert receipt.tender_id == notice_id and receipt.delivery_id == delivery_id
    assert receipt.profile_fingerprint is None  # Historical evidence is not invented.


@pytest.mark.parametrize("currency", [None, "USD", "EUR"])
def test_value_band_requires_known_comparable_currency(currency):
    result = DeterministicMatcher().score(
        company(minimum_contract_value=10000), tender(estimated_value=1000, currency=currency)
    )
    assert result.component_scores["contract_value"] == (0 if currency == "EUR" else None)
