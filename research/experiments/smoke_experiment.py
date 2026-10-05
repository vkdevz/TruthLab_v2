"""Smoke experiment to validate research framework infrastructure.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
from sklearn.linear_model import LogisticRegression

from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


def smoke_experiment_fn(config: ExperimentConfig) -> Dict[str, Any]:
    """Basic deterministic classifier test verifying reproducibility."""
    rng = np.random.RandomState(config.random_seed)
    X = rng.randn(40, 4)
    # Simple synthetic separable rule
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    clf = LogisticRegression(random_state=config.random_seed)
    clf.fit(X[:30], y[:30])
    preds = clf.predict(X[30:])
    accuracy = float(np.mean(preds == y[30:]))

    return {
        "status": "success",
        "test_samples": 10,
        "features": 4,
        "smoke_accuracy": accuracy,
        "coefficients": clf.coef_.tolist(),
        "intercept": clf.intercept_.tolist(),
    }


def main():
    config = ExperimentConfig(
        experiment_id="EXP-01-FRAMEWORK-SMOKE",
        name="framework_smoke_check",
        description="Verify deterministic seed and environment capture",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    result = runner.run(smoke_experiment_fn)
    assert result["results"]["status"] == "success"
    print(f"Smoke experiment verification passed with accuracy: {result['results']['smoke_accuracy']}")


if __name__ == "__main__":
    main()
