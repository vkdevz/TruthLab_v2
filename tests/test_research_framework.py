"""Unit tests for Research Experiment Framework (Commit 01).
"""

from pathlib import Path
from research.configs.config import ExperimentConfig, DatasetConfig, ModelConfig
from research.experiments.runner import (
    ExperimentRunner,
    capture_environment_metadata,
    set_deterministic_seed,
)
from research.experiments.smoke_experiment import smoke_experiment_fn


def test_environment_metadata_capture():
    meta = capture_environment_metadata()
    assert "timestamp_utc" in meta
    assert "python_version" in meta
    assert "git" in meta
    assert "commit" in meta["git"]
    assert "packages" in meta
    assert "scikit-learn" in meta["packages"]


def test_deterministic_seeding():
    set_deterministic_seed(12345)
    import numpy as np
    import random

    r1 = [random.random() for _ in range(5)]
    n1 = np.random.randn(5).tolist()

    set_deterministic_seed(12345)
    r2 = [random.random() for _ in range(5)]
    n2 = np.random.randn(5).tolist()

    assert r1 == r2
    assert n1 == n2


def test_experiment_runner_lifecycle(tmp_path):
    out_dir = tmp_path / "results"
    art_dir = tmp_path / "artifacts"
    config = ExperimentConfig(
        experiment_id="TEST-EXP-01",
        name="test_experiment",
        output_dir=str(out_dir),
        artifacts_dir=str(art_dir),
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(smoke_experiment_fn)

    assert res["experiment_id"] == "TEST-EXP-01"
    assert res["results"]["status"] == "success"
    assert (out_dir / "test_exp_01.json").exists()
