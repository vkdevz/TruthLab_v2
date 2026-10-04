import json
from pathlib import Path
from backend.app.ml.baseline.classifier import BaselineTextClassifier
from backend.app.ml.baseline.dataset_loader import get_curated_benchmark_samples
from backend.app.ml.baseline.evaluate import evaluate_baseline_classifier
from backend.app.core.config import settings


def run_baseline_training() -> dict[str, any]:
    print("=" * 60)
    print("Executing Phase 3: Text Fake-News Baseline Training")
    print("=" * 60)

    train_split, test_split = get_curated_benchmark_samples()
    print(f"Loaded {len(train_split.texts)} training samples and {len(test_split.texts)} held-out test samples.")

    classifier = BaselineTextClassifier()
    print("Fitting TF-IDF + Logistic Regression baseline pipeline...")
    classifier.fit(train_split.texts, train_split.labels)
    print("Model fitting complete.")

    print("\nRunning in-domain and out-of-domain evaluation...")
    train_metrics = evaluate_baseline_classifier(classifier, train_split)
    test_metrics = evaluate_baseline_classifier(classifier, test_split)

    print("\nIn-Domain Train Metrics:")
    for k, v in train_metrics.items():
        print(f"  {k}: {v}")

    print("\nHeld-Out Out-of-Domain Test Metrics:")
    for k, v in test_metrics.items():
        print(f"  {k}: {v}")

    results = {
        "model_type": "TF-IDF (1-2 gram) + Logistic Regression (C=1.0)",
        "in_domain_metrics": train_metrics,
        "out_of_domain_metrics": test_metrics,
    }

    results_path = settings.BASE_DIR / "docs" / "experiments" / "baseline_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nBaseline results logged to: {results_path}")
    return results


if __name__ == "__main__":
    run_baseline_training()
