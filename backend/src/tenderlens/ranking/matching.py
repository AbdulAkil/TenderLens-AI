import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, exists, or_, select
from sqlalchemy.orm import Session, selectinload

from tenderlens.models.company import CompanyProfile, TenderMatch
from tenderlens.models.document import TenderDocument
from tenderlens.models.matching import MatchEvaluation
from tenderlens.models.tender import Tender
from tenderlens.ranking.state import profile_fingerprint

# Preserve the existing relative weights for observable relevance evidence.
# Eligibility is reported separately: a certification mention does not prove it.
WEIGHTS = {
    "capability": 0.35,
    "skills": 0.20,
    "location": 0.10,
    "contract_value": 0.10,
    "cpv": 0.10,
}


def _tokens(value: str) -> set[str]:
    # Preserve the acronym before case folding; the English pronoun "it" is not
    # evidence that a procurement concerns information technology.
    value = re.sub(r"\bIT\b", "software", value)
    value = re.sub(r"\bit services\b", "software services", value)
    value = "".join(
        c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c)
    )
    aliases = {
        "logiciel": "software",
        "logiciels": "software",
        "informatique": "software",
        "informatica": "software",
        "ict": "software",
        "logicielontwikkeling": "software",
        "ontwikkeling": "development",
        "developpement": "development",
        "cybersecurite": "cybersecurity",
        "cyberveiligheid": "cybersecurity",
        "elektrisch": "electrical",
        "elektrische": "electrical",
        "electrique": "electrical",
        "onderhoud": "maintenance",
        "renovatie": "renovation",
        "medisch": "medical",
        "medische": "medical",
        "medicale": "medical",
        "medicaux": "medical",
        "gegevens": "data",
        "donnees": "data",
    }
    stopwords = {
        "the",
        "and",
        "for",
        "of",
        "de",
        "la",
        "le",
        "les",
        "des",
        "et",
        "en",
        "van",
        "het",
        "een",
        "pour",
        "services",
        "it",
        "service",
        "equipment",
        "equipments",
        "materiel",
        "materiaal",
        "solution",
        "solutions",
    }
    return {
        aliases.get(token, token)
        for token in re.findall(r"[a-z0-9]{2,}", value)
        if token not in stopwords
    }


def _normalise(value: str) -> str:
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(c)
        ).split()
    )


def _country(value: str) -> str:
    return {
        "be": "bel",
        "belgium": "bel",
        "belgique": "bel",
        "belgie": "bel",
        "fr": "fra",
        "france": "fra",
        "nl": "nld",
        "netherlands": "nld",
        "nederland": "nld",
        "european union": "eu",
    }.get(_normalise(value), _normalise(value))


def active_tender(now: datetime):
    return (
        Tender.status.not_in(["closed", "cancelled", "planning"]),
        or_(Tender.submission_deadline.is_(None), Tender.submission_deadline > now),
    )


def current_evaluation(company_id, fingerprint):
    return exists(
        select(MatchEvaluation.tender_id).where(
            MatchEvaluation.company_id == company_id,
            MatchEvaluation.tender_id == Tender.id,
            MatchEvaluation.profile_fingerprint == fingerprint,
            MatchEvaluation.tender_version == Tender.match_version,
        )
    )


@dataclass(frozen=True)
class MatchResult:
    component_scores: dict[str, float | None]
    reasons: list[str]
    blockers: list[str]

    @property
    def overall_score(self) -> float:
        # Administrative fit alone must never create a relevant opportunity.
        if not any(
            (self.component_scores.get(key) or 0) > 0 for key in ("capability", "skills", "cpv")
        ):
            return 0.0
        observed = {
            key: weight
            for key, weight in WEIGHTS.items()
            if self.component_scores.get(key) is not None
        }
        denominator = sum(observed.values())
        return (
            round(
                100
                * sum(self.component_scores[key] * weight for key, weight in observed.items())
                / denominator,
                2,
            )
            if denominator
            else 0.0
        )


class DeterministicMatcher:
    def score(self, company: CompanyProfile, tender: Tender) -> MatchResult:
        document_text = " ".join(
            chunk.content for document in tender.documents for chunk in document.chunks
        )
        tender_text = " ".join(filter(None, [tender.title, tender.description, document_text]))
        tender_terms = _tokens(tender_text)
        # Optional prose must not dilute explicit services supplied by the customer.
        capability_terms = (
            _tokens(" ".join(company.services))
            if company.services
            else _tokens(company.description or "")
        )
        shared = sorted(capability_terms & tender_terms)
        capability = len(shared) / len(capability_terms) if capability_terms else None
        skill_hits = [
            skill for skill in company.skills if _tokens(skill) and _tokens(skill) <= tender_terms
        ]
        skills = len(skill_hits) / len(company.skills) if company.skills else None
        countries = {_country(location) for location in company.preferred_locations}
        country = _country(tender.country_code or "")
        location = (
            float(country in countries or "eu" in countries) if countries and country else None
        )
        value = (
            self._value_fit(company, tender.estimated_value)
            if getattr(tender, "currency", None) == "EUR"
            else None
        )
        cpv_hits = [
            code
            for code in company.cpv_codes
            if any(
                candidate.startswith(code.rstrip("0") or code)
                for candidate in tender.cpv_code_values
            )
        ]
        cpv = (
            len(cpv_hits) / len(company.cpv_codes)
            if company.cpv_codes and tender.cpv_code_values
            else None
        )
        reasons, blockers = [], []
        if shared:
            reasons.append(f"Relevant capability terms: {', '.join(shared[:8])}")
        if skill_hits:
            reasons.append(f"Requested skills found: {', '.join(skill_hits[:4])}")
        if cpv_hits:
            reasons.append(f"Published CPV classifications align: {', '.join(cpv_hits)}")
        if location == 1:
            reasons.append(
                "Buyer country aligns with the profile preference; verify place of performance"
            )
        elif location == 0:
            blockers.append(
                "Buyer country differs from the preference; place of performance requires verification"
            )
        if value == 1:
            reasons.append("Published estimated value is within the preferred range")
        if tender.estimated_value is None:
            blockers.append("Information unavailable: contract value is not disclosed")
        if not tender.country_code:
            blockers.append("Information unavailable: buyer country is not disclosed")
        blockers.append("Information unavailable: mandatory eligibility has not been established")
        held = {_normalise(cert) for cert in company.certifications}
        for cert in self._required_certifications(tender_text):
            if _normalise(cert) not in held:
                blockers.append(
                    f"Certification mentioned but not confirmed on the profile: {cert}; verify whether mandatory"
                )
        scores = {
            "capability": capability,
            "skills": skills,
            "location": location,
            "contract_value": value,
            "cpv": cpv,
            "eligibility": None,
        }
        return MatchResult(
            {key: round(score, 4) if score is not None else None for key, score in scores.items()},
            reasons,
            blockers,
        )

    @staticmethod
    def _value_fit(company: CompanyProfile, value: Decimal | None) -> float | None:
        lower, upper = company.minimum_contract_value, company.maximum_contract_value
        if value is None or (lower is None and upper is None):
            return None
        return float((lower is None or value >= lower) and (upper is None or value <= upper))

    @staticmethod
    def _required_certifications(text: str) -> list[str]:
        return [
            certificate
            for certificate in ("ISO 27001", "ISO 9001", "ISO 14001")
            if certificate.casefold() in text.casefold()
        ]

    def excluded(self, company, tender) -> bool:
        text = _normalise(f"{tender.title} {tender.description or ''}")
        return (
            any(_normalise(term) in text for term in (company.exclusions or []) if term.strip())
            or bool(
                company.tender_types
                and tender.procedure_type
                and tender.procedure_type not in company.tender_types
            )
            or (tender.currency == "EUR" and self._value_fit(company, tender.estimated_value) == 0)
        )


@dataclass(frozen=True)
class MatchBatch:
    processed: int
    pending: bool


class MatchService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._matcher = DeterministicMatcher()
        self.last_processed = 0

    def has_pending(self, company) -> bool:
        return (
            self._session.scalar(
                select(Tender.id)
                .where(
                    *active_tender(datetime.now(UTC)),
                    ~current_evaluation(company.id, profile_fingerprint(company)),
                )
                .limit(1)
            )
            is not None
        )

    def process_batch(self, company_id: uuid.UUID, *, batch_size: int = 200) -> MatchBatch:
        if not 1 <= batch_size <= 1000:
            raise ValueError("Matching batch_size must be between 1 and 1000")
        # Serialize competing runs for a profile; source changes remain dirty until
        # their exact version has been evaluated. No timestamp watermark can skip
        # a transaction that commits late.
        company = self._session.scalar(
            select(CompanyProfile)
            .where(CompanyProfile.id == company_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if company is None:
            raise LookupError("Company profile not found")
        fingerprint = profile_fingerprint(company)
        tenders = self._session.scalars(
            select(Tender)
            .where(*active_tender(datetime.now(UTC)), ~current_evaluation(company_id, fingerprint))
            .order_by(Tender.updated_at, Tender.id)
            .limit(batch_size)
            .options(
                selectinload(Tender.documents).selectinload(TenderDocument.chunks),
                selectinload(Tender.cpv_codes),
                selectinload(Tender.buyer),
            )
        ).all()
        ids = [tender.id for tender in tenders]
        previous = {
            row.tender_id: row
            for row in self._session.scalars(
                select(TenderMatch).where(
                    TenderMatch.company_id == company_id, TenderMatch.tender_id.in_(ids)
                )
            )
        }
        evaluations = {
            row.tender_id: row
            for row in self._session.scalars(
                select(MatchEvaluation).where(
                    MatchEvaluation.company_id == company_id, MatchEvaluation.tender_id.in_(ids)
                )
            )
        }
        for tender in tenders:
            match = previous.get(tender.id)
            result = (
                None
                if self._matcher.excluded(company, tender)
                else self._matcher.score(company, tender)
            )
            if result is None or result.overall_score == 0:
                if match is not None:
                    self._session.delete(match)
            else:
                if match is None:
                    match = TenderMatch(company_id=company_id, tender_id=tender.id)
                    self._session.add(match)
                match.overall_score = result.overall_score
                match.component_scores = result.component_scores
                match.reasons, match.blockers = result.reasons, result.blockers
                match.calculated_at = datetime.now(UTC)
            evaluation = evaluations.get(tender.id)
            if evaluation is None:
                evaluation = MatchEvaluation(company_id=company_id, tender_id=tender.id)
                self._session.add(evaluation)
            evaluation.profile_fingerprint = fingerprint
            evaluation.tender_updated_at = tender.updated_at
            evaluation.tender_version = tender.match_version
            evaluation.evaluated_at = datetime.now(UTC)
        active = select(Tender.id).where(*active_tender(datetime.now(UTC)))
        self._session.execute(
            delete(TenderMatch).where(
                TenderMatch.company_id == company_id, TenderMatch.tender_id.not_in(active)
            )
        )
        self._session.commit()
        return MatchBatch(len(tenders), self.has_pending(company))

    def calculate_for_company(
        self, company_id: uuid.UUID, *, batch_size: int = 200, max_batches: int | None = None
    ) -> list[TenderMatch]:
        batches = 0
        self.last_processed = 0
        while True:
            result = self.process_batch(company_id, batch_size=batch_size)
            batches += 1
            self.last_processed += result.processed
            if not result.pending or (max_batches is not None and batches >= max_batches):
                break
        # Response size is bounded independently from the corpus traversal.
        from tenderlens.repositories.companies import CompanyRepository

        company = self._session.get(CompanyProfile, company_id)
        return CompanyRepository(self._session, company.organization_id).list_matches(
            company_id, limit=100
        )
