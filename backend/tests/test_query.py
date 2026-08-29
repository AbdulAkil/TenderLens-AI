from tenderlens.retrieval.query import evidence_query


def test_evidence_query_removes_common_question_terms() -> None:
    assert (
        evidence_query("Which lot covers Tietomallikoordinaattoripalvelut?")
        == "tietomallikoordinaattoripalvelut"
    )
