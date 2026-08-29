from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from tenderlens.ingestion.exceptions import TedResponseError


@dataclass(frozen=True)
class NormalizedTender:
    source: str
    source_id: str
    source_url: str
    title: str
    raw_metadata: dict[str, Any]
    description: str | None = None
    buyer_name: str | None = None
    buyer_country_code: str | None = None
    cpv_codes: tuple[str, ...] = ()
    publication_date: datetime | None = None
    submission_deadline: datetime | None = None
    estimated_value: Decimal | None = None
    currency: str | None = None
    procedure_type: str | None = None


def normalize_ted_notice(notice: dict[str, Any]) -> NormalizedTender:
    """Normalize a TED search projection while preserving the unmodified source payload."""
    source_id = _first_text(notice, "publication-number", "publicationNumber", "notice-id")
    title = _localized_text(notice.get("title-proc")) or _localized_text(notice.get("notice-title"))
    if not source_id or not title:
        raise TedResponseError("TED notice is missing the requested publication number or title")

    return NormalizedTender(
        source="ted",
        source_id=source_id,
        source_url=_preferred_notice_url(notice.get("links"), source_id),
        title=title,
        description=_localized_text(notice.get("notice-title")),
        buyer_name=_localized_text(notice.get("buyer-name")),
        buyer_country_code=_first_scalar(notice.get("buyer-country")),
        cpv_codes=_normalized_cpv_codes(notice.get("classification-cpv")),
        publication_date=_parse_ted_date(
            _first_text(notice, "publication-date", "publicationDate")
        ),
        submission_deadline=_parse_ted_date(_first_text(notice, "deadline")),
        estimated_value=_parse_decimal(_first_scalar(notice.get("estimated-value-proc"))),
        currency=_first_scalar(notice.get("estimated-value-cur-proc")),
        procedure_type=_first_scalar(notice.get("procedure-type")),
        raw_metadata=notice,
    )


def _first_text(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _localized_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if not isinstance(value, dict):
        return None
    for language in ("eng", "en"):
        text = _first_scalar(value.get(language))
        if text:
            return text
    for translated_value in value.values():
        text = _first_scalar(translated_value)
        if text:
            return text
    return None


def _first_scalar(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, list):
        for item in value:
            text = _first_scalar(item)
            if text:
                return text
    return None


def _normalized_cpv_codes(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict.fromkeys(item for item in value if isinstance(item, str) and item.strip()))


def _parse_ted_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # TED Search's date-only values may carry a UTC offset without a time.
        # Preserve the original string in raw_metadata; store only a UTC date boundary.
        return datetime.combine(date.fromisoformat(value[:10]), time.min, tzinfo=UTC)
    except ValueError:
        return None


def _parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _preferred_notice_url(links: Any, source_id: str) -> str:
    if isinstance(links, dict):
        for format_name in ("html", "htmlDirect", "xml"):
            links_by_language = links.get(format_name)
            if not isinstance(links_by_language, dict):
                continue
            for language in ("ENG", "eng", "MUL"):
                url = links_by_language.get(language)
                if isinstance(url, str) and url:
                    return url
            for url in links_by_language.values():
                if isinstance(url, str) and url:
                    return url
    return f"https://ted.europa.eu/en/notice/-/detail/{source_id}"
