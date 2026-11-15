"""PostgreSQL-backed scheduled worker. Run as a dedicated always-on service."""

import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import structlog
from fastapi import HTTPException
from sqlalchemy import delete, or_, select, text
from sqlalchemy.orm import Session

from tenderlens.config import get_settings
from tenderlens.database.session import SessionLocal
from tenderlens.ingestion.runner import TedIngestionRunner
from tenderlens.ingestion.ted_client import TedClient
from tenderlens.models.company import CompanyProfile, SavedTender, TenderMatch
from tenderlens.models.tender import Tender
from tenderlens.ranking.matching import MatchService
from tenderlens.saas.email import deliver_pending, queue_email, safe_link
from tenderlens.saas.models import (
    ActionToken,
    AuthSession,
    Delivery,
    Job,
    Membership,
    NotificationPreference,
    Organization,
    RateBucket,
    TenderFeedback,
    User,
)
from tenderlens.saas.plans import entitlement
from tenderlens.schemas.ingestion import TedIngestionRequest

logger = structlog.get_logger(__name__)


def enqueue(session: Session, kind: str, key: str, payload: dict | None = None):
    if not session.scalar(select(Job.id).where(Job.dedup_key == key)):
        session.add(Job(kind=kind, dedup_key=key, payload=payload or {}))
        session.flush()


def schedule(session: Session) -> None:
    now = datetime.now(UTC)
    # A transactional advisory lock coordinates multiple schedulers.
    if session.bind.dialect.name == "postgresql":
        if not session.scalar(text("SELECT pg_try_advisory_xact_lock(72381946)")):
            return
    hour = now.strftime("%Y-%m-%dT%H")
    day = now.date().isoformat()
    if get_settings().ted_ingestion_enabled:
        # Replay a rolling publication window; unchanged notices do no downstream work.
        enqueue(
            session,
            "ingest",
            f"ingest:{hour}",
            {"since": (now - timedelta(days=3)).strftime("%Y%m%d")},
        )
    enqueue(session, "match", f"match:{hour}")
    enqueue(session, "analyze", f"analyze:{hour}")
    enqueue(session, "digest", f"digest:{hour}")
    enqueue(session, "reminders", f"reminders:{hour}")
    enqueue(session, "changes", f"changes:{hour}")
    enqueue(session, "cleanup", f"cleanup:{day}")
    session.commit()


def build_digests(session: Session) -> int:
    from tenderlens.models.matching import DigestOpportunity
    from tenderlens.ranking.matching import current_evaluation
    from tenderlens.ranking.state import profile_fingerprint
    from tenderlens.saas.digest_state import digest_is_current, invalidate_draft

    now = datetime.now(UTC)
    generated = 0
    for pref, user, org in session.execute(
        select(NotificationPreference, User, Organization)
        .join(User, User.id == NotificationPreference.user_id)
        .join(Organization, Organization.id == NotificationPreference.organization_id)
        .where(
            User.verified.is_(True),
            NotificationPreference.frequency != "off",
            Organization.deletion_requested_at.is_(None),
        )
    ).all():
        if not session.get(Membership, (user.id, org.id)):
            continue
        try:
            plan = entitlement(org)
        except HTTPException:
            continue
        session.refresh(pref, with_for_update=True)
        daily = pref.frequency == "daily" and plan.daily
        local = now.astimezone(ZoneInfo(pref.timezone))
        period = (
            local.strftime("%Y-%m-%d")
            if daily
            else f"{local.isocalendar().year}-W{local.isocalendar().week:02}"
        )
        key = f"digest:{org.id}:{user.id}:{period}"
        existing = session.scalar(select(Delivery).where(Delivery.dedup_key == key))
        if existing:
            if existing.status in {"review", "pending"} and not digest_is_current(
                session, existing
            ):
                invalidate_draft(session, existing)
                if existing.attempts or existing.provider_id:
                    continue
            else:
                continue
        companies = session.scalars(
            select(CompanyProfile).where(CompanyProfile.organization_id == org.id)
        ).all()
        service = MatchService(session)
        if any(service.has_pending(company) for company in companies):
            continue
        best = {}
        for company in companies:
            dismissed = select(TenderFeedback.tender_id).where(
                TenderFeedback.company_id == company.id,
                TenderFeedback.value.in_(
                    ["irrelevant", "not_eligible", "not_interested", "applied"]
                ),
            )
            assigned = select(DigestOpportunity.tender_id).where(
                DigestOpportunity.organization_id == org.id, DigestOpportunity.user_id == user.id
            )
            matches = session.scalars(
                select(TenderMatch)
                .join(Tender)
                .where(
                    TenderMatch.company_id == company.id,
                    TenderMatch.overall_score >= pref.minimum_score,
                    current_evaluation(company.id, profile_fingerprint(company)),
                    Tender.status.not_in(["closed", "cancelled", "planning"]),
                    or_(Tender.submission_deadline.is_(None), Tender.submission_deadline > now),
                    Tender.id.not_in(dismissed),
                    Tender.id.not_in(assigned),
                )
                .order_by(TenderMatch.overall_score.desc(), Tender.id)
                .limit(10)
            ).all()
            for match in matches:
                if (
                    match.tender_id not in best
                    or match.overall_score > best[match.tender_id][1].overall_score
                ):
                    best[match.tender_id] = (company, match)
        selected = sorted(
            best.values(), key=lambda pair: (-float(pair[1].overall_score), str(pair[1].tender_id))
        )[:10]
        if not selected:
            continue
        entries = []
        for company, match in selected:
            tender = match.tender
            entries.append(
                f"{company.name}: {tender.title}\nBuyer: {tender.buyer_name or 'Not disclosed'}\nBuyer country: {tender.country_code or 'Not disclosed'}\nValue: {str(tender.estimated_value) + ' ' + (tender.currency or 'currency unavailable') if tender.estimated_value is not None else 'Not disclosed'}\nLatest known entry deadline (verify each lot): {tender.submission_deadline.isoformat() if tender.submission_deadline else 'Not disclosed'}\nRelevance: {match.overall_score}/100 (experimental deterministic score; unknown components excluded)\nWhy: {'; '.join(match.reasons)}\nVerify: {'; '.join(match.blockers)}\nOfficial source: {safe_link(tender.source_url) or 'Source requires verification'}\nWorkspace: {get_settings().site_url}/tenders/{tender.id}"
            )
        body = (
            f"{org.name} — reporting period {period}\n{len(selected)} opportunities newly discovered for your profile. They may have been published earlier.\n\n"
            + "\n\n---\n\n".join(entries)
        )
        body += f"\n\nManage or unsubscribe from tender notifications: {get_settings().site_url}/notifications"
        delivery = queue_email(
            session,
            user=user,
            organization_id=org.id,
            key=key,
            category="digest",
            subject=f"{len(selected)} procurement opportunities for {org.name}"[:256],
            text=body,
            action_url=f"{get_settings().site_url}/dashboard",
        )
        for company, match in selected:
            session.add(
                DigestOpportunity(
                    organization_id=org.id,
                    user_id=user.id,
                    tender_id=match.tender_id,
                    delivery_id=delivery.id,
                    company_id=company.id,
                    profile_fingerprint=profile_fingerprint(company),
                    tender_version=match.tender.match_version,
                )
            )
        session.flush()
        generated += 1
    session.commit()
    return generated


def build_reminders(session: Session) -> int:
    now = datetime.now(UTC)
    generated = 0
    rows = session.execute(
        select(SavedTender, CompanyProfile, Tender)
        .join(CompanyProfile)
        .join(Tender, SavedTender.tender_id == Tender.id)
        .where(
            Tender.submission_deadline > now, Tender.submission_deadline <= now + timedelta(days=3)
        )
    ).all()
    for saved, company, tender in rows:
        org = session.get(Organization, company.organization_id)
        if not org or org.deletion_requested_at:
            continue
        try:
            entitlement(org, "daily")
        except HTTPException:
            continue
        for _pref, user in session.execute(
            select(NotificationPreference, User)
            .join(User)
            .where(
                NotificationPreference.organization_id == org.id,
                NotificationPreference.deadline_reminders.is_(True),
                NotificationPreference.frequency != "off",
                User.verified.is_(True),
            )
        ).all():
            if not session.get(Membership, (user.id, org.id)):
                continue
            key = f"deadline:{user.id}:{saved.id}:{tender.submission_deadline.isoformat()}"
            queue_email(
                session,
                user=user,
                organization_id=org.id,
                key=key,
                category="deadline",
                subject=f"Deadline approaching: {tender.title}"[:256],
                text=f"{company.name}\n{tender.title}\nOfficial deadline: {tender.submission_deadline.isoformat()}\nVerify submission requirements at {safe_link(tender.source_url) or 'the official source'}.\nPreferences: {get_settings().site_url}/notifications",
                action_url=f"{get_settings().site_url}/tenders/{tender.id}",
            )
            generated += 1
    session.commit()
    return generated


def build_change_notifications(session: Session) -> int:
    from tenderlens.saas.models import NoticeRevision

    now = datetime.now(UTC)
    generated = 0
    rows = session.execute(
        select(SavedTender, CompanyProfile, Tender, NoticeRevision)
        .join(CompanyProfile, SavedTender.company_id == CompanyProfile.id)
        .join(Tender, SavedTender.tender_id == Tender.id)
        .join(NoticeRevision, NoticeRevision.tender_id == Tender.id)
        .where(
            NoticeRevision.created_at > SavedTender.created_at,
            NoticeRevision.created_at >= now - timedelta(days=7),
        )
        .order_by(NoticeRevision.created_at)
        .limit(1000)
    ).all()
    for saved, company, tender, revision in rows:
        org = session.get(Organization, company.organization_id)
        if not org or org.deletion_requested_at:
            continue
        try:
            entitlement(org)
        except HTTPException:
            continue
        for _pref, user in session.execute(
            select(NotificationPreference, User)
            .join(User)
            .where(
                NotificationPreference.organization_id == org.id,
                NotificationPreference.updates.is_(True),
                NotificationPreference.frequency != "off",
                User.verified.is_(True),
            )
        ).all():
            if not session.get(Membership, (user.id, org.id)):
                continue
            category = "cancellation" if tender.status == "cancelled" else "update"
            queue_email(
                session,
                user=user,
                organization_id=org.id,
                key=f"change:{saved.id}:{revision.id}:{user.id}",
                category=category,
                subject=f"{'Cancelled' if category == 'cancellation' else 'Updated'}: {tender.title}"[
                    :256
                ],
                text=f"{company.name}\nThe saved notice has a new source revision.\nChanged source fields: {', '.join(sorted(revision.changes))}\nCurrent source status: {tender.status}\nReview the official record: {safe_link(tender.source_url) or 'Source requires verification'}\nPreferences: {get_settings().site_url}/notifications",
                action_url=f"{get_settings().site_url}/tenders/{tender.id}",
            )
            generated += 1
    session.commit()
    return generated


async def execute_job(job: Job, session: Session) -> dict:
    if job.kind == "ingest":
        settings = get_settings()
        query = f"({settings.ingestion_query}) AND publication-date >= {job.payload['since']}"
        async with TedClient(settings) as client:
            result = await TedIngestionRunner(session, client).run(
                TedIngestionRequest(
                    query=query, scope="ALL", max_notices=settings.ingestion_max_notices
                )
            )
        if not result.complete:
            raise RuntimeError(
                "Ingestion window truncated: use smaller backfill windows or raise the configured notice bound"
            )
        return result.model_dump()
    if job.kind == "match":
        cursor = None
        queued = 0
        while True:
            query = (
                select(CompanyProfile)
                .join(Organization)
                .where(Organization.deletion_requested_at.is_(None))
                .order_by(CompanyProfile.id)
                .limit(100)
            )
            if cursor is not None:
                query = query.where(CompanyProfile.id > cursor)
            companies = session.scalars(query).all()
            if not companies:
                break
            for company in companies:
                try:
                    entitlement(session.get(Organization, company.organization_id))
                except HTTPException:
                    continue
                enqueue(
                    session,
                    "match_company",
                    f"company:{job.dedup_key}:{company.id}",
                    {"company_id": str(company.id)},
                )
                queued += 1
            cursor = companies[-1].id
            session.commit()
        return {"profiles_queued": queued}
    if job.kind == "match_company":
        import uuid

        company = session.get(CompanyProfile, uuid.UUID(job.payload["company_id"]))
        if company is None:
            return {"deleted": True}
        org = session.get(Organization, company.organization_id)
        if not org or org.deletion_requested_at:
            return {"inactive": True}
        try:
            entitlement(org)
        except HTTPException:
            return {"inactive": True}
        result = MatchService(session).process_batch(company.id)
        if result.pending:
            enqueue(session, "match_company", f"continue:{job.id}:{company.id}", job.payload)
        else:
            enqueue(session, "digest", f"digest:matched:{job.id}")
        session.commit()
        return {"processed": result.processed, "pending": result.pending}
    if job.kind == "digest":
        return {"digests": build_digests(session)}
    if job.kind == "analyze":
        if not get_settings().document_processing_enabled:
            return {"processed": 0, "disabled": True}
        from tenderlens.analysis.service import TenderAnalysisService, TenderExtractionService
        from tenderlens.documents.processing import TenderDocumentProcessor

        ids = session.scalars(
            select(TenderMatch.tender_id)
            .where(TenderMatch.overall_score >= 40)
            .order_by(TenderMatch.overall_score.desc())
            .limit(20)
        ).all()
        processed = 0
        for tender_id in list(dict.fromkeys(ids))[:5]:
            await TenderDocumentProcessor(session).process_notice_document(tender_id)
            await TenderExtractionService(session).extract(tender_id)
            TenderAnalysisService(session).generate(tender_id)
            processed += 1
        return {"processed": processed, "method": "rules"}
    if job.kind == "reminders":
        return {"reminders": build_reminders(session)}
    if job.kind == "changes":
        return {"notifications": build_change_notifications(session)}
    if job.kind == "cleanup":
        now = datetime.now(UTC)
        for model in [AuthSession, ActionToken, RateBucket]:
            session.execute(delete(model).where(model.expires_at < now))
        session.execute(
            delete(Delivery).where(
                Delivery.created_at < now - timedelta(days=90),
                Delivery.status.in_(["dry_run", "sent", "failed", "suppressed"]),
            )
        )
        session.execute(
            delete(Job).where(Job.created_at < now - timedelta(days=90), Job.status == "done")
        )
        session.commit()
        return {"cleaned": True}
    raise ValueError("Unknown job kind")


async def tick() -> None:
    with SessionLocal() as session:
        schedule(session)
        now = datetime.now(UTC)
        from sqlalchemy import update

        session.execute(
            update(Job)
            .where(Job.status == "running", Job.lease_until < now, Job.attempts >= 5)
            .values(status="failed", last_error="Lease expired after final attempt")
        )
        session.commit()
        job = session.scalar(
            select(Job)
            .where(
                or_(
                    (Job.status == "pending") & (Job.available_at <= now),
                    (Job.status == "running") & (Job.lease_until < now),
                ),
                Job.attempts < 5,
            )
            .order_by(Job.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if job:
            job.status = "running"
            job.attempts += 1
            job.lease_until = now + timedelta(minutes=15)
            job_id = job.id
            session.commit()
            try:
                # Timeout ends before lease expiry; one worker is the supported deployment.
                result = await asyncio.wait_for(execute_job(job, session), timeout=600)
                job = session.get(Job, job_id)
                job.status, job.result, job.last_error = "done", result, None
            except Exception as exc:
                session.rollback()
                job = session.get(Job, job_id)
                job.status = "failed" if job.attempts >= 5 else "pending"
                job.available_at = datetime.now(UTC) + timedelta(minutes=2**job.attempts)
                job.last_error = type(exc).__name__
                logger.error(
                    "worker_job_failed",
                    job_id=str(job.id),
                    kind=job.kind,
                    error_type=type(exc).__name__,
                )
            session.commit()
        await deliver_pending(session)


async def run(once=False):
    while True:
        try:
            await tick()
        except Exception as exc:
            logger.error("worker_tick_failed", error_type=type(exc).__name__)
            if once:
                raise
        if once:
            return
        await asyncio.sleep(get_settings().worker_poll_seconds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.once))


if __name__ == "__main__":
    main()
