"""Unit tests for Temporal Verification Benchmark (Commit 08).
"""

from pathlib import Path
from research.experiments.temporal_benchmark import run_temporal_benchmark


def test_temporal_benchmark_execution():
    res = run_temporal_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    metrics = res["results"]["metrics"]

    assert metrics["present_framing_detection_accuracy"] >= 0.90
    assert metrics["outdated_claim_recall"] >= 0.80
    assert metrics["event_vs_publication_separation_rate"] == 1.0
    assert len(res["results"]["explicit_assumptions"]) >= 3
    assert Path("research/results/temporal_benchmark.json").exists()
