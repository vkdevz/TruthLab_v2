"""Unit tests for Statistical Significance Analysis (Commit 15).
"""

from pathlib import Path
import numpy as np
from research.experiments.statistical_significance import (
    compute_mcnemar_test,
    run_statistical_significance,
)


def test_mcnemar_exact_binomial_computation():
    gold = np.array([1, 1, 1, 0, 0])
    base = np.array([1, 0, 0, 0, 0])  # 2 correct
    sys = np.array([1, 1, 1, 0, 0])   # 5 correct

    res = compute_mcnemar_test(gold, base, sys)
    assert res["test_name"] == "McNemar's Exact Binomial Test"
    assert res["contingency_table"]["both_correct_a"] == 3
    assert res["contingency_table"]["sys_only_correct_c"] == 2
    assert 0.0 <= res["two_tailed_p_value"] <= 1.0


def test_statistical_significance_execution():
    res = run_statistical_significance()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    assert "bootstrap_results" in res["results"]
    assert "hypothesis_testing" in res["results"]
    assert "scientific_interpretation" in res["results"]
    assert Path("research/results/statistical_significance.json").exists()
