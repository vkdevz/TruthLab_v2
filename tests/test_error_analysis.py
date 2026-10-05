"""Unit tests for Systematic Error Analysis (Commit 14).
"""

from pathlib import Path
from research.experiments.error_analysis import run_error_analysis


def test_error_analysis_execution():
    res = run_error_analysis()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    assert "total_test_samples" in res["results"]
    assert "category_counts" in res["results"]
    assert "failure_cases" in res["results"]

    assert Path("research/results/error_analysis.json").exists()
    assert Path("docs/experiments/ERROR_ANALYSIS.md").exists()
