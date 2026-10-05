"""Reproducible Experiment Execution Framework.

Captures environment metadata, hardware properties, git revisions,
and ensures deterministic random seeding for all research experiments.
"""

from __future__ import annotations

import datetime
import importlib.metadata
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import numpy as np

from research.configs.config import ExperimentConfig


def set_deterministic_seed(seed: int = 42) -> None:
    """Set seeds across Python standard library, NumPy, and environment."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def capture_environment_metadata() -> Dict[str, Any]:
    """Capture precise runtime, git, package, and hardware metadata."""
    git_commit = "unknown"
    git_branch = "unknown"
    git_dirty = False
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
        git_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
        diff = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL
        ).decode().strip()
        git_dirty = len(diff) > 0
    except Exception:
        pass

    packages_to_track = [
        "scikit-learn",
        "scipy",
        "numpy",
        "pillow",
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "matplotlib",
        "trafilatura",
    ]
    package_versions = {}
    for pkg in packages_to_track:
        try:
            package_versions[pkg] = importlib.metadata.version(pkg)
        except Exception:
            package_versions[pkg] = "not-installed"

    return {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "git": {
            "commit": git_commit,
            "branch": git_branch,
            "dirty": git_dirty,
        },
        "packages": package_versions,
    }


class ExperimentRunner:
    """Manages experiment execution lifecycle and result tracking."""

    def __init__(self, config: Optional[ExperimentConfig] = None):
        self.config = config or ExperimentConfig()
        self.output_dir = Path(self.config.output_dir)
        self.artifacts_dir = Path(self.config.artifacts_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        experiment_fn: Callable[..., Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute an experiment under strictly controlled conditions."""
        set_deterministic_seed(self.config.random_seed)
        env_meta = capture_environment_metadata()
        start_time = time.perf_counter()

        print(f"[*] Running Experiment: {self.config.experiment_id} ({self.config.name})")
        print(f"[*] Random Seed: {self.config.random_seed}")
        print(f"[*] Git Commit: {env_meta['git']['commit'][:8]} (dirty={env_meta['git']['dirty']})")

        # Execute experiment logic
        results = experiment_fn(self.config, **kwargs)

        elapsed_seconds = round(time.perf_counter() - start_time, 4)
        print(f"[+] Completed in {elapsed_seconds}s")

        output_payload = {
            "experiment_id": self.config.experiment_id,
            "name": self.config.name,
            "description": self.config.description,
            "config": self.config.to_dict(),
            "environment": env_meta,
            "elapsed_seconds": elapsed_seconds,
            "results": results,
        }

        output_file = self.output_dir / f"{self.config.experiment_id.lower().replace('-', '_')}.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

        print(f"[+] Results saved to: {output_file}")
        return output_payload
