from datetime import UTC, datetime

from sqlalchemy import delete, select

from tenderlens.models.company import CompanyProfile, TenderMatch
from tenderlens.models.matching import DigestOpportunity
from tenderlens.models.tender import Tender
from tenderlens.ranking.state import profile_fingerprint
from tenderlens.saas.models import NotificationPreference, TenderFeedback
from tenderlens.saas.security import aware


def digest_is_current(session, delivery) -> bool:
    preference = session.get(NotificationPreference, (delivery.user_id, delivery.organization_id))
    if not preference:
        return False
    items = session.scalars(
        select(DigestOpportunity).where(DigestOpportunity.delivery_id == delivery.id)
    ).all()
    if not items:
        return False
    for item in items:
        tender = session.get(Tender, item.tender_id)
        company = session.get(CompanyProfile, item.company_id) if item.company_id else None
        if (
            not tender
            or tender.status in {"closed", "cancelled", "planning"}
            or (
                tender.submission_deadline
                and aware(tender.submission_deadline) <= datetime.now(UTC)
            )
        ):
            return False
        if (
            not company
            or company.organization_id != delivery.organization_id
            or item.profile_fingerprint != profile_fingerprint(company)
            or item.tender_version != tender.match_version
        ):
            return False
        match = session.scalar(
            select(TenderMatch).where(
                TenderMatch.company_id == company.id,
                TenderMatch.tender_id == tender.id,
            )
        )
        dismissed = session.scalar(
            select(TenderFeedback.id).where(
                TenderFeedback.company_id == company.id,
                TenderFeedback.tender_id == tender.id,
                TenderFeedback.value.in_(
                    ["irrelevant", "not_eligible", "not_interested", "applied"]
                ),
            )
        )
        if not match or match.overall_score < preference.minimum_score or dismissed:
            return False
    return True


def invalidate_draft(session, delivery):
    if delivery.attempts or delivery.provider_id:
        delivery.status = "review"
        delivery.last_error = (
            "Source/profile changed after an attempted send; operator review required"
        )
        return
    delivery.status = "stale"
    delivery.last_error = "Source, profile or deadline changed; draft will be regenerated"
    delivery.dedup_key = f"{delivery.dedup_key}:stale:{delivery.id}"
    session.execute(delete(DigestOpportunity).where(DigestOpportunity.delivery_id == delivery.id))
    session.flush()
