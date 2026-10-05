"""Unit tests for Text Baseline Benchmark (Commit 04).
"""

from pathlib import Path
from research.configs.config import ExperimentConfig
from research.experiments.text_baseline import run_text_baseline_benchmark


def test_text_baseline_benchmark_execution():
    res = run_text_baseline_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    models = res["results"]["models"]

    assert "tfidf_logistic_regression" in models
    assert "tfidf_naive_bayes" in models
    assert "majority_class_prior" in models

    lr_res = models["tfidf_logistic_regression"]["binary"]
    assert 0.0 <= lr_res["accuracy"] <= 1.0
    assert 0.0 <= lr_res["macro_f1"] <= 1.0
    assert "confusion_matrix" in lr_res

    lr_5 = models["tfidf_logistic_regression"]["five_class"]
    assert 0.0 <= lr_5["accuracy"] <= 1.0
    assert len(lr_5["classes"]) == 5
    assert (Path("research/results/text_baseline_benchmark.json")).exists()
