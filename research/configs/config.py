"""Reproducible Experiment Configuration Schema.

Provides structured configurations for experiments, datasets, models,
and evaluation suites with strict reproducibility guarantees.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DatasetConfig:
    name: str = "curated_verification_benchmark"
    source_path: str = "data/benchmark/text_baseline_benchmark.json"
    claim_reviews_path: str = "data/claim_reviews/reference_claim_reviews.json"
    modalities: List[str] = field(default_factory=lambda: ["text", "image", "video"])
    train_ratio: float = 0.6
    val_ratio: float = 0.2
    test_ratio: float = 0.2
    stratified: bool = True
    random_seed: int = 42


@dataclass
class ModelConfig:
    baseline_type: str = "tfidf_logistic_regression"
    ngram_range: tuple = (1, 2)
    max_features: int = 5000
    regularization_c: float = 1.0
    class_weight: str = "balanced"
    calibrator: str = "temperature_scaling"
    temperature: float = 1.15
    fusion_strategy: str = "calibrated_decision_matrix"


@dataclass
class ExperimentConfig:
    experiment_id: str = "EXP-DEFAULT"
    name: str = "reproducible_experiment"
    description: str = "Default reproducible benchmark configuration"
    random_seed: int = 42
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    output_dir: str = "research/results"
    artifacts_dir: str = "research/artifacts"
    save_predictions: bool = True
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, filepath: str | Path) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str | Path) -> ExperimentConfig:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset_cfg = DatasetConfig(**data.get("dataset", {}))
        model_cfg = ModelConfig(**data.get("model", {}))
        data["dataset"] = dataset_cfg
        data["model"] = model_cfg
        return cls(**data)
