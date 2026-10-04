import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.baseline.classifier import BaselineTextClassifier
from backend.app.ml.baseline.dataset_loader import get_curated_benchmark_samples
from backend.app.ml.baseline.evaluate import evaluate_baseline_classifier, compute_expected_calibration_error
import numpy as np


def test_baseline_classifier_fit_and_predict():
    train_split, test_split = get_curated_benchmark_samples()
    classifier = BaselineTextClassifier()
    classifier.fit(train_split.texts, train_split.labels)

    # Predict on clear sensational text
    pred = classifier.predict("SHOCKING: Secret alien base uncovered in presidential palace!")
    assert pred.label == "FAKE"
    assert pred.fake_probability > 0.50
    assert 0.0 <= pred.confidence <= 1.0
    assert round(pred.real_probability + pred.fake_probability, 2) == 1.0
    assert len(pred.top_predictive_cues) > 0

    # Predict on neutral administrative text
    pred_real = classifier.predict("The central bank held interest rates steady following monthly policy meeting.")
    assert pred_real.label == "REAL"
    assert pred_real.real_probability > 0.50


def test_baseline_evaluation_metrics():
    train_split, test_split = get_curated_benchmark_samples()
    classifier = BaselineTextClassifier()
    classifier.fit(train_split.texts, train_split.labels)

    metrics = evaluate_baseline_classifier(classifier, test_split)
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "ece" in metrics
    assert 0.0 <= metrics["ece"] <= 1.0


def test_ece_computation_synthetic():
    # Perfectly calibrated dummy predictions
    probs = np.array([[0.8, 0.2], [0.2, 0.8], [0.9, 0.1], [0.1, 0.9]])
    y_true = np.array([0, 1, 0, 1])
    ece = compute_expected_calibration_error(probs, y_true, num_bins=5)
    assert 0.0 <= ece <= 0.25


@pytest.mark.asyncio
async def test_baseline_api_predict():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/baseline/predict", json={
            "text": "URGENT ALERT: Drinking boiled garlic water cures all viral infections overnight!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "FAKE"
        assert "baseline_disclaimer" in data
        assert len(data["top_predictive_cues"]) > 0
