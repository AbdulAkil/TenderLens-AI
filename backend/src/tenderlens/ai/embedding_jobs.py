import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from tenderlens.ai.embeddings import EmbeddingProvider
from tenderlens.models.document import DocumentChunk, TenderDocument


class EmbeddingJob:
    def __init__(self, session: Session, provider: EmbeddingProvider) -> None:
        self._session = session
        self._provider = provider

    async def embed_tender_chunks(self, tender_id: uuid.UUID, batch_size: int = 32) -> int:
        chunks = self._session.scalars(
            select(DocumentChunk)
            .join(TenderDocument, DocumentChunk.document_id == TenderDocument.id)
            .where(TenderDocument.tender_id == tender_id, DocumentChunk.embedding.is_(None))
            .order_by(DocumentChunk.chunk_index)
        ).all()
        for offset in range(0, len(chunks), batch_size):
            batch = chunks[offset : offset + batch_size]
            vectors = await self._provider.embed([chunk.content for chunk in batch])
            if len(vectors) != len(batch) or any(len(vector) != 1536 for vector in vectors):
                raise RuntimeError("Embedding provider did not return 1536-dimensional vectors")
            for chunk, vector in zip(batch, vectors, strict=True):
                chunk.embedding = vector
            self._session.commit()
        return len(chunks)
