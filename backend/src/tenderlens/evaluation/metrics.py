from collections.abc import Sequence


def reciprocal_rank(relevant: Sequence[bool]) -> float:
    for rank, is_relevant in enumerate(relevant, start=1):
        if is_relevant:
            return 1 / rank
    return 0.0


def recall_at_k(relevant: Sequence[bool], k: int) -> float:
    return float(any(relevant[:k]))


def mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None
