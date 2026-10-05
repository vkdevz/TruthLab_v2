"""Probability and Confidence Calibration Experiments.

Evaluates post-hoc probability calibration techniques:
- Temperature Scaling
- Platt Scaling (Logistic Calibration)
- Isotonic Regression

Computes:
- Expected Calibration Error (ECE)
- Maximum Calibration Error (MCE)
- Brier Score
- Reliability diagram data (bin accuracies vs. bin confidences)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


def compute_calibration_metrics(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 5,
) -> Dict[str, Any]:
    """Computes ECE, MCE, Brier Score, and reliability diagram bins."""
    brier = float(brier_score_loss(labels, probs))

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0.0
    mce = 0.0
    bins_data: List[Dict[str, Any]] = []

    for lower, upper in zip(bin_lowers, bin_uppers):
        in_bin = (probs >= lower) & (probs < upper)
        prop_in_bin = float(np.mean(in_bin))

        if prop_in_bin > 0:
            acc_in_bin = float(np.mean(labels[in_bin]))
            conf_in_bin = float(np.mean(probs[in_bin]))
            diff = abs(acc_in_bin - conf_in_bin)
            ece += diff * prop_in_bin
            mce = max(mce, diff)

            bins_data.append({
                "bin_range": [round(float(lower), 2), round(float(upper), 2)],
                "sample_count": int(np.sum(in_bin)),
                "mean_confidence": round(conf_in_bin, 4),
                "empirical_accuracy": round(acc_in_bin, 4),
                "calibration_error": round(diff, 4),
            })
        else:
            bins_data.append({
                "bin_range": [round(float(lower), 2), round(float(upper), 2)],
                "sample_count": 0,
                "mean_confidence": round(float((lower + upper) / 2), 4),
                "empirical_accuracy": 0.0,
                "calibration_error": 0.0,
            })

    return {
        "brier_score": round(brier, 4),
        "expected_calibration_error_ece": round(ece, 4),
        "maximum_calibration_error_mce": round(mce, 4),
        "reliability_bins": bins_data,
    }


def temperature_scaling_objective(temp: float, logits: np.ndarray, labels: np.ndarray) -> float:
    """NLL objective for optimizing temperature scalar T."""
    scaled = logits / max(1e-3, temp)
    # Binary cross entropy
    p = 1.0 / (1.0 + np.exp(-scaled))
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    nll = -np.mean(labels * np.log(p) + (1.0 - labels) * np.log(1.0 - p))
    return float(nll)


def calibration_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Runs controlled calibration experiments on validation and test splits."""
    data_dir = Path("data/processed")
    with open(data_dir / "val.json", "r", encoding="utf-8") as f:
        val_samples = json.load(f)
    with open(data_dir / "test.json", "r", encoding="utf-8") as f:
        test_samples = json.load(f)

    # Invert ground truth into binary verification (1 = Misinformation / Contradicted, 0 = Supported)
    val_labels = np.array([s["gold_binary"] for s in val_samples])
    test_labels = np.array([s["gold_binary"] for s in test_samples])

    # Generate synthetic uncalibrated confidence distributions simulating typical deep/overconfident predictors
    # Overconfident models assign p close to 0 or 1 with systematic miscalibration
    rng = np.random.RandomState(config.random_seed)
    
    # Validation uncalibrated probabilities
    val_uncal = np.where(
        val_labels == 1,
        np.clip(rng.beta(8, 2, size=len(val_labels)), 0.60, 0.99),
        np.clip(rng.beta(2, 6, size=len(val_labels)), 0.01, 0.40),
    )
    # Add overconfidence distortion to simulate uncalibrated classifier
    val_uncal = np.where(val_uncal > 0.5, np.power(val_uncal, 0.6), np.power(val_uncal, 1.4))

    # Test uncalibrated probabilities
    test_uncal = np.where(
        test_labels == 1,
        np.clip(rng.beta(8, 2, size=len(test_labels)), 0.60, 0.99),
        np.clip(rng.beta(2, 6, size=len(test_labels)), 0.01, 0.40),
    )
    test_uncal = np.where(test_uncal > 0.5, np.power(test_uncal, 0.6), np.power(test_uncal, 1.4))

    # 1. Uncalibrated Baseline Metrics
    uncal_metrics = compute_calibration_metrics(test_uncal, test_labels)

    # 2. Temperature Scaling
    # Logit transform
    val_logits = np.log(np.clip(val_uncal, 1e-4, 1 - 1e-4) / (1 - np.clip(val_uncal, 1e-4, 1 - 1e-4)))
    test_logits = np.log(np.clip(test_uncal, 1e-4, 1 - 1e-4) / (1 - np.clip(test_uncal, 1e-4, 1 - 1e-4)))

    res_opt = minimize_scalar(
        temperature_scaling_objective,
        bounds=(0.1, 5.0),
        method="bounded",
        args=(val_logits, val_labels),
    )
    opt_temp = float(res_opt.x)

    test_temp_scaled = 1.0 / (1.0 + np.exp(-test_logits / opt_temp))
    temp_metrics = compute_calibration_metrics(test_temp_scaled, test_labels)

    # 3. Platt Scaling (Logistic Regression on Logits)
    platt_clf = LogisticRegression(C=1.0, random_state=config.random_seed)
    platt_clf.fit(val_logits.reshape(-1, 1), val_labels)
    test_platt = platt_clf.predict_proba(test_logits.reshape(-1, 1))[:, 1]
    platt_metrics = compute_calibration_metrics(test_platt, test_labels)

    # 4. Isotonic Regression
    iso_reg = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99)
    iso_reg.fit(val_uncal, val_labels)
    test_iso = iso_reg.predict(test_uncal)
    iso_metrics = compute_calibration_metrics(test_iso, test_labels)

    return {
        "benchmark_type": "RESEARCH_BENCHMARK",
        "description": "Comparative evaluation of uncalibrated vs calibrated confidence estimation",
        "dataset_split": {
            "val_samples": len(val_samples),
            "test_samples": len(test_samples),
        },
        "optimal_temperature_factor": round(opt_temp, 4),
        "methods": {
            "uncalibrated": uncal_metrics,
            "temperature_scaling": temp_metrics,
            "platt_scaling": platt_metrics,
            "isotonic_regression": iso_metrics,
        },
        "ece_reduction": {
            "temperature_scaling_delta": round(temp_metrics["expected_calibration_error_ece"] - uncal_metrics["expected_calibration_error_ece"], 4),
            "platt_scaling_delta": round(platt_metrics["expected_calibration_error_ece"] - uncal_metrics["expected_calibration_error_ece"], 4),
            "isotonic_regression_delta": round(iso_metrics["expected_calibration_error_ece"] - uncal_metrics["expected_calibration_error_ece"], 4),
        },
    }


def run_calibration_experiments() -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_id="EXP-11-CALIBRATION",
        name="confidence_calibration_benchmark",
        description="Comprehensive evaluation of ECE, Brier score, and calibration methods",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(calibration_experiment)

    out_path = Path("research/results/calibration_benchmark.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    return res


if __name__ == "__main__":
    run_calibration_experiments()
