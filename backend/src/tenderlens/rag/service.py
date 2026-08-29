import uuid

from sqlalchemy.orm import Session

from tenderlens.ai.embeddings import EmbeddingProvider
from tenderlens.ai.llm import LLMProvider
from tenderlens.ai.reranker import KeywordReranker, Reranker
from tenderlens.repositories.retrieval import RetrievalRepository
from tenderlens.retrieval.query import evidence_query
from tenderlens.retrieval.service import HybridRetriever
from tenderlens.schemas.analysis import CitationRead, TenderAnswer


class TenderQuestionService:
    def __init__(
        self,
        session: Session,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        llm_provider: LLMProvider | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self._retriever = HybridRetriever(RetrievalRepository(session), embedding_provider)
        self._llm_provider = llm_provider
        self._reranker = reranker or KeywordReranker()

    async def ask(self, tender_id: uuid.UUID, question: str) -> TenderAnswer:
        hits = await self._retriever.search(evidence_query(question), limit=12, tender_id=tender_id)
        hits = self._reranker.rerank(question, hits, limit=5)
        citations = [
            CitationRead(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                source_url=hit.source_url,
                page_number=hit.page_number,
                section=hit.section,
                excerpt=hit.content[:500],
            )
            for hit in hits
        ]
        method = (
            "hybrid"
            if self._llm_provider and any("semantic" in hit.method for hit in hits)
            else "lexical"
        )
        if not hits:
            return TenderAnswer(
                answer="Insufficient source evidence is available to answer this question.",
                status="insufficient_evidence",
                citations=[],
                retrieval_method=method,
            )
        if self._llm_provider is None:
            return TenderAnswer(
                answer=(
                    "A generated answer is disabled. The source excerpts below are the evidence "
                    "retrieved for this question."
                ),
                status="evidence_only",
                citations=citations,
                retrieval_method=method,
            )
        context = "\n\n".join(
            f"[Source {index + 1}; chunk {hit.chunk_id}]\n{hit.content}"
            for index, hit in enumerate(hits)
        )
        result = await self._llm_provider.answer(
            instructions=(
                "Answer the procurement question only from the supplied source excerpts. "
                "If the answer is not explicitly supported, say that evidence is insufficient. "
                "Do not give legal advice. Refer to sources by their source number."
            ),
            input_text=f"Question: {question}\n\nEvidence:\n{context}",
        )
        return TenderAnswer(
            answer=result.text,
            status="answered",
            citations=citations,
            retrieval_method=method,
            model=result.model,
        )
