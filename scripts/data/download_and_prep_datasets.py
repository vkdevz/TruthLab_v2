"""Dataset Preparation and Ingestion Script for Phase 1.
Exports and formats local benchmark datasets and ClaimReview reference indices.
"""

import json
from pathlib import Path
from backend.app.services.retrieval.factcheck_cache import REFERENCE_CLAIM_REVIEWS
from backend.app.ml.baseline.dataset_loader import get_curated_benchmark_samples

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def prepare_datasets():
    print(f"Preparing datasets in: {DATA_DIR}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    claim_reviews_dir = DATA_DIR / "claim_reviews"
    claim_reviews_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir = DATA_DIR / "benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export Reference ClaimReview records
    claim_review_path = claim_reviews_dir / "reference_claim_reviews.json"
    with open(claim_review_path, "w", encoding="utf-8") as f:
        json.dump(REFERENCE_CLAIM_REVIEWS, f, indent=2)
    print(f"Exported {len(REFERENCE_CLAIM_REVIEWS)} ClaimReview records to {claim_review_path}")

    # 2. Export Curated Baseline Benchmark Split
    train_split, test_split = get_curated_benchmark_samples()
    benchmark_data = {
        "train": [{"text": t, "label": l} for t, l in zip(train_split.texts, train_split.labels)],
        "test": [{"text": t, "label": l} for t, l in zip(test_split.texts, test_split.labels)],
    }
    benchmark_path = benchmark_dir / "text_baseline_benchmark.json"
    with open(benchmark_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"Exported {len(train_split.texts)} train and {len(test_split.texts)} test samples to {benchmark_path}")

    print("Dataset preparation complete.")


if __name__ == "__main__":
    prepare_datasets()
