import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from backend.app.ml.baseline.classifier import BaselineTextClassifier
from backend.app.ml.baseline.dataset_loader import DatasetSplit


def compute_expected_calibration_error(
    probabilities: np.ndarray,
    ground_truth: np.ndarray,
    num_bins: int = 10
) -> float:
    """Computes Expected Calibration Error (ECE) across B equal-width confidence bins."""
    confidences = np.max(probabilities, axis=1)
    predictions = np.argmax(probabilities, axis=1)
    accuracies = (predictions == ground_truth).astype(float)

    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    n = len(ground_truth)

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            bin_accuracy = np.mean(accuracies[in_bin])
            bin_confidence = np.mean(confidences[in_bin])
            ece += np.abs(bin_accuracy - bin_confidence) * prop_in_bin

    return float(round(ece, 4))


def evaluate_baseline_classifier(
    classifier: BaselineTextClassifier,
    split: DatasetSplit
) -> dict[str, float | list]:
    """Runs full benchmark evaluation on a test split."""
    predictions = []
    fake_probs = []
    real_probs = []

    for text in split.texts:
        pred = classifier.predict(text)
        pred_label_int = 1 if pred.label == "FAKE" else 0
        predictions.append(pred_label_int)
        fake_probs.append(pred.fake_probability)
        real_probs.append(pred.real_probability)

    y_true = np.array(split.labels)
    y_pred = np.array(predictions)
    prob_matrix = np.column_stack([real_probs, fake_probs])

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()
    ece = compute_expected_calibration_error(prob_matrix, y_true)

    return {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "macro_f1": round(float(macro_f1), 4),
        "ece": round(float(ece), 4),
        "confusion_matrix": cm,
        "sample_count": len(y_true),
    }
