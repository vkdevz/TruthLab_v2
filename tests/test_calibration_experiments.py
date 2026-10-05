"""Unit tests for Calibration Experiments (Commit 11).
"""

from pathlib import Path
import numpy as np
from research.experiments.calibration_experiments import (
    compute_calibration_metrics,
    run_calibration_experiments,
)


def test_compute_calibration_metrics():
    # Perfectly calibrated case: 10 samples with conf 1.0 that are all 1s
    probs = np.array([1.0] * 10)
    labels = np.array([1] * 10)
    metrics = compute_calibration_metrics(probs, labels, n_bins=5)
    assert metrics["brier_score"] == 0.0
    assert metrics["expected_calibration_error_ece"] == 0.0


def test_calibration_experiments_execution():
    res = run_calibration_experiments()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    methods = res["results"]["methods"]

    assert "uncalibrated" in methods
    assert "temperature_scaling" in methods
    assert "platt_scaling" in methods
    assert "isotonic_regression" in methods

    for m_name, m_val in methods.items():
        assert 0.0 <= m_val["brier_score"] <= 1.0
        assert 0.0 <= m_val["expected_calibration_error_ece"] <= 1.0
        assert len(m_val["reliability_bins"]) == 5

    assert Path("research/results/calibration_benchmark.json").exists()
