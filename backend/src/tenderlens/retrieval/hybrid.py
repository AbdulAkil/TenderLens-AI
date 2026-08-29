from collections.abc import Iterable

from tenderlens.retrieval.types import RetrievalHit


def reciprocal_rank_fusion(
    result_sets: Iterable[list[RetrievalHit]],
    *,
    rank_constant: int = 60,
    limit: int = 20,
) -> list[RetrievalHit]:
    """Fuse ranked lists deterministically without treating model scores as comparable."""
    scores: dict[object, float] = {}
    hits: dict[object, RetrievalHit] = {}
    methods: dict[object, set[str]] = {}
    for result_set in result_sets:
        for rank, hit in enumerate(result_set, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0) + 1 / (rank_constant + rank)
            hits[hit.chunk_id] = hit
            methods.setdefault(hit.chunk_id, set()).add(hit.method)
    ranked_ids = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)[:limit]
    return [
        RetrievalHit(
            **{
                **hits[chunk_id].__dict__,
                "score": scores[chunk_id],
                "method": "+".join(sorted(methods[chunk_id])),
            }
        )
        for chunk_id in ranked_ids
    ]
