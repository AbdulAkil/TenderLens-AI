from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from tenderlens.database.session import SessionLocal
from tenderlens.evaluation.metrics import mean, recall_at_k, reciprocal_rank
from tenderlens.models.tender import Tender
from tenderlens.repositories.retrieval import RetrievalRepository
from tenderlens.retrieval.query import evidence_query


@dataclass(frozen=True)
class EvaluationCase:
    source_id: str
    question: str
    expected_answer: str
    expected_evidence_terms: list[str]

    @classmethod
    def from_dict(cls, item: dict[str, object]) -> EvaluationCase:
        return cls(
            source_id=str(item["source_id"]),
            question=str(item["question"]),
            expected_answer=str(item["expected_answer"]),
            expected_evidence_terms=[str(term) for term in item["expected_evidence_terms"]],
        )


def load_cases(dataset_dir: Path) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    for path in sorted(dataset_dir.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                cases.append(EvaluationCase.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"Invalid evaluation case in {path.name}:{line_number}") from exc
    return cases


def run_retrieval_evaluation(cases: list[EvaluationCase]) -> dict[str, object]:
    per_case: list[dict[str, object]] = []
    with SessionLocal() as session:
        repository = RetrievalRepository(session)
        for case in cases:
            tender = session.scalar(select(Tender).where(Tender.source_id == case.source_id))
            if tender is None:
                per_case.append(
                    {
                        "source_id": case.source_id,
                        "question": case.question,
                        "status": "not_ingested",
                    }
                )
                continue
            hits = repository.lexical(evidence_query(case.question), limit=5, tender_id=tender.id)
            relevance = [
                all(term.lower() in hit.content.lower() for term in case.expected_evidence_terms)
                for hit in hits
            ]
            per_case.append(
                {
                    "source_id": case.source_id,
                    "question": case.question,
                    "status": "evaluated",
                    "retrieved_chunk_ids": [str(hit.chunk_id) for hit in hits],
                    "recall_at_1": recall_at_k(relevance, 1),
                    "recall_at_5": recall_at_k(relevance, 5),
                    "mrr": reciprocal_rank(relevance),
                }
            )
    evaluated = [item for item in per_case if item["status"] == "evaluated"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "method": "lexical",
        "cases_total": len(cases),
        "cases_evaluated": len(evaluated),
        "recall_at_1": mean([float(item["recall_at_1"]) for item in evaluated]),
        "recall_at_5": mean([float(item["recall_at_5"]) for item in evaluated]),
        "mrr": mean([float(item["mrr"]) for item in evaluated]),
        "per_case": per_case,
    }


def write_report(dataset_dir: Path, reports_dir: Path) -> Path:
    report = run_retrieval_evaluation(load_cases(dataset_dir))
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"retrieval-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
