import uuid

from tenderlens.ai.embeddings import EmbeddingProvider
from tenderlens.repositories.retrieval import RetrievalRepository
from tenderlens.retrieval.hybrid import reciprocal_rank_fusion
from tenderlens.retrieval.types import RetrievalHit


class HybridRetriever:
    def __init__(
        self,
        repository: RetrievalRepository,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        tender_id: uuid.UUID | None = None,
    ) -> list[RetrievalHit]:
        lexical_hits = self._repository.lexical(query, limit * 2, tender_id)
        if self._embedding_provider is None:
            return lexical_hits[:limit]
        embedding = (await self._embedding_provider.embed([query]))[0]
        semantic_hits = self._repository.semantic(embedding, limit * 2, tender_id)
        return reciprocal_rank_fusion([lexical_hits, semantic_hits], limit=limit)
