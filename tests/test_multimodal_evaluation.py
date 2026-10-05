"""Unit tests for Multimodal Evaluation Benchmark (Commit 09).
"""

from pathlib import Path
from research.experiments.multimodal_evaluation import run_multimodal_benchmark


def test_multimodal_benchmark_execution():
    res = run_multimodal_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    assert res["results"]["multimodal_sample_count"] == 19
    assert "cross_modal_alignment" in res["results"]
    assert "performance_comparison" in res["results"]

    align = res["results"]["cross_modal_alignment"]
    assert 0.0 <= align["mean_alignment_score"] <= 1.0
    assert align["flagged_disparities_count"] >= 0

    assert Path("research/results/multimodal_benchmark.json").exists()
