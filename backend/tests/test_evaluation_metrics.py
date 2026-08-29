from tenderlens.evaluation.metrics import mean, recall_at_k, reciprocal_rank


def test_retrieval_metrics_are_deterministic() -> None:
    relevance = [False, True, False]

    assert recall_at_k(relevance, 1) == 0
    assert recall_at_k(relevance, 5) == 1
    assert reciprocal_rank(relevance) == 0.5
    assert mean([1.0, 0.5]) == 0.75
