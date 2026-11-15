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


def precision_at_k(relevant: Sequence[bool], k: int) -> float | None:
    if k <= 0:
        raise ValueError("k must be positive")
    selected = relevant[:k]
    return sum(selected) / len(selected) if selected else None


def false_positive_rate(predicted: Sequence[bool], relevant: Sequence[bool]) -> float | None:
    if len(predicted) != len(relevant):
        raise ValueError("Prediction and relevance labels must align")
    negatives = sum(not label for label in relevant)
    return (
        sum(pred and not label for pred, label in zip(predicted, relevant, strict=True)) / negatives
        if negatives
        else None
    )


def useful_match_rate(useful: Sequence[bool]) -> float | None:
    return sum(useful) / len(useful) if useful else None
