import uuid

from tenderlens.retrieval.hybrid import reciprocal_rank_fusion
from tenderlens.retrieval.types import RetrievalHit


def _hit(chunk_id: uuid.UUID, score: float, method: str) -> RetrievalHit:
    return RetrievalHit(
        chunk_id=chunk_id,
        tender_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        content="source text",
        source_url="https://ted.europa.eu/en/notice/1-2026/xml",
        score=score,
        page_number=None,
        section=None,
        method=method,
    )


def test_reciprocal_rank_fusion_rewards_hits_shared_by_methods() -> None:
    shared = uuid.uuid4()
    lexical_only = uuid.uuid4()
    semantic_only = uuid.uuid4()

    fused = reciprocal_rank_fusion(
        [
            [_hit(lexical_only, 0.9, "lexical"), _hit(shared, 0.8, "lexical")],
            [_hit(shared, 0.9, "semantic"), _hit(semantic_only, 0.8, "semantic")],
        ]
    )

    assert fused[0].chunk_id == shared
    assert fused[0].method == "lexical+semantic"
