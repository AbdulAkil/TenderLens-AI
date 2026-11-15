from decimal import Decimal

from tenderlens.ingestion.normalization import normalize_ted_notice


def test_normalizes_ted_identity_and_retains_source_payload() -> None:
    source = {
        "publication-number": "556964-2026",
        "title-proc": {"nld": "Studieopdracht: Heraanleg en uitbreiding"},
        "notice-title": {"eng": "Belgium – Architectural services"},
        "buyer-name": {"nld": ["Gemeentebestuur Knokke-Heist"]},
        "buyer-country": ["BEL"],
        "publication-date": "2026-08-12+02:00",
        "deadline": "2026-09-21",
        "procedure-type": "open",
        "classification-cpv": ["71000000", "71000000"],
        "estimated-value-proc": "380000.00",
        "estimated-value-cur-proc": "EUR",
        "links": {"html": {"ENG": "https://ted.europa.eu/en/notice/-/detail/556964-2026"}},
    }

    tender = normalize_ted_notice(source)

    assert tender.source == "ted"
    assert tender.source_id == "556964-2026"
    assert tender.title == "Studieopdracht: Heraanleg en uitbreiding"
    assert tender.description == "Belgium – Architectural services"
    assert tender.buyer_name == "Gemeentebestuur Knokke-Heist"
    assert tender.buyer_country_code == "BEL"
    assert tender.cpv_codes == ("71000000",)
    assert tender.estimated_value == Decimal("380000.00")
    assert tender.currency == "EUR"
    assert tender.source_url.endswith("556964-2026")
    assert tender.raw_metadata == source


def test_ted_lot_deadlines_use_earliest_known_instant():
    source = {
        "publication-number": "test",
        "title-proc": {"eng": "Test notice"},
        "deadline": ["2026-12-02T12:00:00+01:00", "2026-12-01T10:30:00Z"],
    }
    tender = normalize_ted_notice(source)
    assert tender.submission_deadline.isoformat() == "2026-12-01T10:30:00+00:00"
