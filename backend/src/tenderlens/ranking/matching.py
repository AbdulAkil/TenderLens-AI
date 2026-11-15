import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from tenderlens.models.company import CompanyProfile, TenderMatch
from tenderlens.models.document import TenderDocument
from tenderlens.models.tender import Tender


def _tokens(value: str) -> set[str]:
    value = "".join(
        c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c)
    )
    aliases = {
        "logiciel": "software",
        "logiciels": "software",
        "informatique": "software",
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
        "service",
    }
    return {
        aliases.get(token, token)
        for token in re.findall(r"[a-z0-9]{2,}", value)
        if token not in stopwords
    }


def _normalise(value: str) -> str:
    return " ".join(value.lower().split())


@dataclass(frozen=True)
class MatchResult:
    component_scores: dict[str, float]
    reasons: list[str]
    blockers: list[str]

    @property
    def overall_score(self) -> float:
        weights = {
            "capability": 0.35,
            "skills": 0.20,
            "location": 0.10,
            "contract_value": 0.10,
            "eligibility": 0.15,
            "cpv": 0.10,
        }
        return round(
            sum(self.component_scores[key] * weight for key, weight in weights.items()) * 100, 2
        )


class DeterministicMatcher:
    def score(self, company: CompanyProfile, tender: Tender) -> MatchResult:
        document_text = " ".join(
            chunk.content for document in tender.documents for chunk in document.chunks
        )
        tender_text = " ".join(filter(None, [tender.title, tender.description, document_text]))
        capability_terms = _tokens(
            " ".join([company.description or "", *company.services, *company.industries])
        )
        tender_terms = _tokens(tender_text)
        shared_capabilities = sorted(capability_terms & tender_terms)
        capability = (
            len(shared_capabilities) / max(1, min(len(capability_terms), 12))
            if capability_terms
            else 0
        )
        skill_hits = [
            skill for skill in company.skills if _normalise(skill) in _normalise(tender_text)
        ]
        skills = len(skill_hits) / len(company.skills) if company.skills else 0

        locations = {_normalise(location) for location in company.preferred_locations}
        country_aliases = {
            "belgium": "bel",
            "belgique": "bel",
            "belgie": "bel",
            "european union": "eu",
            "eu": "eu",
        }
        tender_country = (tender.country_code or "").lower()
        location = 0
        if locations:
            normalized_locations = {country_aliases.get(loc, loc) for loc in locations}
            location = (
                1.0
                if tender_country and (tender_country in normalized_locations or "eu" in locations)
                else 0.0
            )
            location = max(
                location,
                float(country_aliases.get("belgium") == tender_country and "belgium" in locations),
            )

        value = self._value_fit(company, tender.estimated_value)
        tender_cpvs = set(tender.cpv_code_values)
        cpv = (
            len(tender_cpvs & set(company.cpv_codes)) / len(company.cpv_codes)
            if company.cpv_codes
            else 0
        )
        required_certifications = self._required_certifications(tender_text)
        held_certifications = {_normalise(item) for item in company.certifications}
        missing_certifications = [
            certificate
            for certificate in required_certifications
            if _normalise(certificate) not in held_certifications
        ]
        eligibility = (
            (len(required_certifications) - len(missing_certifications))
            / len(required_certifications)
            if required_certifications
            else 0
        )

        scores = {
            "capability": round(min(capability, 1.0), 3),
            "skills": round(min(skills, 1.0), 3),
            "location": round(location, 3),
            "contract_value": round(value, 3),
            "eligibility": round(eligibility, 3),
            "cpv": round(min(cpv, 1.0), 3),
        }
        reasons = []
        if shared_capabilities:
            reasons.append(f"Relevant capability terms: {', '.join(shared_capabilities[:4])}")
        if skill_hits:
            reasons.append(f"Requested skills found: {', '.join(skill_hits[:4])}")
        if scores["location"] == 1:
            reasons.append("Delivery geography matches the company preference")
        if scores["contract_value"] == 1:
            reasons.append("Estimated contract value is within the preferred range")
        blockers = [
            f"Possible requirement not listed on company profile: {item}"
            for item in missing_certifications
        ]
        if not required_certifications:
            blockers.append(
                "Information unavailable: mandatory eligibility has not been established"
            )
        if tender.estimated_value is None:
            blockers.append("Information unavailable: contract value is not disclosed")
        if scores["location"] == 0:
            blockers.append("Tender geography is outside the company preference")
        return MatchResult(component_scores=scores, reasons=reasons, blockers=blockers)

    @staticmethod
    def _value_fit(company: CompanyProfile, value: Decimal | None) -> float:
        if value is None or (
            company.minimum_contract_value is None and company.maximum_contract_value is None
        ):
            return 0
        lower = company.minimum_contract_value
        upper = company.maximum_contract_value
        if (lower is None or value >= lower) and (upper is None or value <= upper):
            return 1.0
        return 0.0

    @staticmethod
    def _required_certifications(text: str) -> list[str]:
        lowered = _normalise(text)
        known = ["ISO 27001", "ISO 9001", "ISO 14001"]
        return [certificate for certificate in known if certificate.lower() in lowered]


class MatchService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._matcher = DeterministicMatcher()

    def calculate_for_company(
        self, company_id: uuid.UUID, *, limit: int = 1000
    ) -> list[TenderMatch]:
        company = self._session.get(CompanyProfile, company_id)
        if company is None:
            raise LookupError("Company profile not found")
        tenders = self._session.scalars(
            select(Tender)
            .where(
                (Tender.submission_deadline.is_(None))
                | (Tender.submission_deadline > datetime.now(UTC))
            )
            .order_by(Tender.ingested_at.desc())
            .limit(limit)
            .options(
                selectinload(Tender.documents).selectinload(TenderDocument.chunks),
                selectinload(Tender.cpv_codes),
                selectinload(Tender.buyer),
            )
        ).all()
        matches: list[TenderMatch] = []
        # Remove stale matches for excluded or expired notices. Rebuild selected
        # candidates transactionally; saved opportunities remain independent.
        accepted_ids = []
        for tender in tenders:
            text = f"{tender.title} {tender.description or ''}".lower()
            if any(term.lower() in text for term in (company.exclusions or []) if term.strip()):
                continue
            if (
                company.tender_types
                and tender.procedure_type
                and tender.procedure_type not in company.tender_types
            ):
                continue
            if (
                tender.estimated_value is not None
                and self._matcher._value_fit(company, tender.estimated_value) == 0
                and (
                    company.minimum_contract_value is not None
                    or company.maximum_contract_value is not None
                )
            ):
                continue
            result = self._matcher.score(company, tender)
            if (
                company.preferred_locations
                and tender.country_code
                and result.component_scores["location"] == 0
            ):
                continue
            accepted_ids.append(tender.id)
            match = self._session.scalar(
                select(TenderMatch).where(
                    TenderMatch.company_id == company.id, TenderMatch.tender_id == tender.id
                )
            )
            from tenderlens.saas.security import aware

            if match and aware(match.calculated_at) >= max(
                aware(company.updated_at), aware(tender.updated_at)
            ):
                matches.append(match)
                continue
            if match is None:
                match = TenderMatch(company_id=company.id, tender_id=tender.id)
                self._session.add(match)
            match.overall_score = result.overall_score
            match.component_scores = result.component_scores
            match.reasons = result.reasons
            match.blockers = result.blockers
            matches.append(match)
        self._session.execute(
            delete(TenderMatch).where(
                TenderMatch.company_id == company.id, TenderMatch.tender_id.not_in(accepted_ids)
            )
        )
        self._session.commit()
        for match in matches:
            self._session.refresh(match)
        return sorted(matches, key=lambda item: item.overall_score, reverse=True)
