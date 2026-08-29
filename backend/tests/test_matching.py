from types import SimpleNamespace

from tenderlens.ranking.matching import DeterministicMatcher


def test_matcher_returns_explainable_scores_and_blockers() -> None:
    company = SimpleNamespace(
        description="AI and data engineering consultancy",
        services=["AI consulting", "data engineering"],
        industries=[],
        skills=["Python", "machine learning"],
        preferred_locations=["BEL"],
        minimum_contract_value=20_000,
        maximum_contract_value=500_000,
        cpv_codes=[],
        certifications=[],
    )
    tender = SimpleNamespace(
        title="AI data engineering services",
        description="Python delivery requires ISO 27001.",
        documents=[],
        country_code="BEL",
        estimated_value=100_000,
        cpv_code_values=[],
    )

    result = DeterministicMatcher().score(company, tender)

    assert result.overall_score > 50
    assert result.component_scores["location"] == 1
    assert result.component_scores["contract_value"] == 1
    assert any("ISO 27001" in blocker for blocker in result.blockers)
