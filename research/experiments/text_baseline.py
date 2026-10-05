"""Formal Text Baseline Benchmark.

Evaluates surface-level text-only classification models:
- TF-IDF + Logistic Regression
- TF-IDF + Multinomial Naive Bayes
- Majority Class Prior (Zero-Rule Baseline)

Computes Accuracy, Precision, Recall, Macro-F1, per-class breakdown,
and Confusion Matrix on real audited dataset splits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


def evaluate_classifier_model(
    model: Any,
    train_texts: List[str],
    train_labels: List[Any],
    test_texts: List[str],
    test_labels: List[Any],
    classes: List[Any],
) -> Dict[str, Any]:
    """Train and comprehensively evaluate a text classification model."""
    model.fit(train_texts, train_labels)
    preds = model.predict(test_texts)

    acc = float(accuracy_score(test_labels, preds))
    macro_p = float(precision_score(test_labels, preds, average="macro", zero_division=0))
    macro_r = float(recall_score(test_labels, preds, average="macro", zero_division=0))
    macro_f1 = float(f1_score(test_labels, preds, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(test_labels, preds, average="weighted", zero_division=0))

    cm = confusion_matrix(test_labels, preds, labels=classes).tolist()
    report = classification_report(
        test_labels, preds, labels=classes, output_dict=True, zero_division=0
    )

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "confusion_matrix": cm,
        "classes": [str(c) for c in classes],
        "classification_report": report,
        "predictions": [str(p) for p in preds],
        "gold_targets": [str(t) for t in test_labels],
    }


def text_baseline_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Execute formal text-only baseline benchmark on audited splits."""
    data_dir = Path("data/processed")
    with open(data_dir / "train.json", "r", encoding="utf-8") as f:
        train_samples = json.load(f)
    with open(data_dir / "test.json", "r", encoding="utf-8") as f:
        test_samples = json.load(f)

    train_texts = [s["text"] for s in train_samples]
    test_texts = [s["text"] for s in test_samples]

    train_bin = [s["gold_binary"] for s in train_samples]
    test_bin = [s["gold_binary"] for s in test_samples]

    train_5class = [s["gold_verdict"] for s in train_samples]
    test_5class = [s["gold_verdict"] for s in test_samples]

    class_labels_5 = ["SUPPORTED", "CONTRADICTED", "MISLEADING", "OUTDATED", "INSUFFICIENT_EVIDENCE"]
    class_labels_bin = [0, 1]

    # Model Pipelines
    # 1. TF-IDF + Logistic Regression
    pipe_lr_bin = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
        ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=config.random_seed, class_weight="balanced")),
    ])
    pipe_lr_5 = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
        ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=config.random_seed, class_weight="balanced")),
    ])

    # 2. TF-IDF + Multinomial Naive Bayes
    pipe_nb_bin = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
        ("clf", MultinomialNB(alpha=1.0)),
    ])
    pipe_nb_5 = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
        ("clf", MultinomialNB(alpha=1.0)),
    ])

    # 3. Majority Class Baseline
    dummy_bin = DummyClassifier(strategy="most_frequent")
    dummy_5 = DummyClassifier(strategy="most_frequent")

    # Evaluations
    res_lr_bin = evaluate_classifier_model(pipe_lr_bin, train_texts, train_bin, test_texts, test_bin, class_labels_bin)
    res_lr_5 = evaluate_classifier_model(pipe_lr_5, train_texts, train_5class, test_texts, test_5class, class_labels_5)

    res_nb_bin = evaluate_classifier_model(pipe_nb_bin, train_texts, train_bin, test_texts, test_bin, class_labels_bin)
    res_nb_5 = evaluate_classifier_model(pipe_nb_5, train_texts, train_5class, test_texts, test_5class, class_labels_5)

    res_dummy_bin = evaluate_classifier_model(dummy_bin, train_texts, train_bin, test_texts, test_bin, class_labels_bin)
    res_dummy_5 = evaluate_classifier_model(dummy_5, train_texts, train_5class, test_texts, test_5class, class_labels_5)

    return {
        "benchmark_type": "RESEARCH_BENCHMARK",
        "description": "Text-only baseline evaluation on verified benchmark split without external evidence retrieval",
        "dataset_split": {
            "train_samples": len(train_samples),
            "test_samples": len(test_samples),
        },
        "models": {
            "tfidf_logistic_regression": {
                "binary": res_lr_bin,
                "five_class": res_lr_5,
            },
            "tfidf_naive_bayes": {
                "binary": res_nb_bin,
                "five_class": res_nb_5,
            },
            "majority_class_prior": {
                "binary": res_dummy_bin,
                "five_class": res_dummy_5,
            },
        },
    }


def run_text_baseline_benchmark() -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_id="EXP-04-TEXT-BASELINE",
        name="text_baseline_benchmark",
        description="Formal Text-Only Baseline Benchmark (TF-IDF + LR, TF-IDF + MNB, Majority Prior)",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(text_baseline_experiment)
    # Also save dedicated research result file
    dedicated_out = Path("research/results/text_baseline_benchmark.json")
    dedicated_out.parent.mkdir(parents=True, exist_ok=True)
    with open(dedicated_out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    return res


if __name__ == "__main__":
    run_text_baseline_benchmark()
