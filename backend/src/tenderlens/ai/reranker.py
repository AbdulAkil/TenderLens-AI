import re
from typing import Protocol

from tenderlens.retrieval.types import RetrievalHit


class Reranker(Protocol):
    def rerank(self, query: str, hits: list[RetrievalHit], limit: int) -> list[RetrievalHit]: ...


class KeywordReranker:
    """Deterministic fallback reranker that needs no additional provider."""

    def rerank(self, query: str, hits: list[RetrievalHit], limit: int) -> list[RetrievalHit]:
        query_terms = set(re.findall(r"[a-z0-9]{2,}", query.lower()))
        ranked = sorted(
            hits,
            key=lambda hit: (
                len(query_terms & set(re.findall(r"[a-z0-9]{2,}", hit.content.lower()))),
                hit.score,
            ),
            reverse=True,
        )
        return ranked[:limit]
