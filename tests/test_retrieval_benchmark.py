"""Unit tests for Evidence Retrieval Benchmark (Commit 06).
"""

from pathlib import Path
from research.experiments.retrieval_benchmark import (
    compute_retrieval_metrics,
    run_retrieval_benchmark,
)


def test_retrieval_metrics_calculation():
    # 2 queries, 1 relevant item each at rank 1 and rank 2
    mock_rel = [
        [1, 0, 0],
        [0, 1, 0],
    ]
    metrics = compute_retrieval_metrics(mock_rel, k_values=(1, 2, 3))
    assert metrics["mrr"] == 0.75  # (1.0 + 0.5) / 2
    assert metrics["recall@1"] == 0.5
    assert metrics["recall@2"] == 1.0


def test_retrieval_benchmark_execution():
    res = run_retrieval_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    assert "metrics" in res["results"]
    raw_m = res["results"]["metrics"]["raw_semantic_retrieval"]

    assert 0.0 <= raw_m["mrr"] <= 1.0
    assert 0.0 <= raw_m["recall@1"] <= 1.0
    assert 0.0 <= raw_m["recall@5"] <= 1.0
    assert Path("research/results/retrieval_benchmark.json").exists()
