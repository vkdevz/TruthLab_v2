from pathlib import Path
from dataclasses import dataclass
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from backend.app.core.config import settings


@dataclass
class BaselinePrediction:
    label: str  # "REAL" or "FAKE"
    fake_probability: float
    real_probability: float
    confidence: float
    top_predictive_cues: list[dict[str, float | str]]
    explanation: str


class BaselineTextClassifier:
    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path or (settings.BASE_DIR / "models" / "checkpoints" / "baseline_tfidf_lr.joblib")
        self.pipeline: Pipeline | None = None
        self._load_or_initialize()

    def _load_or_initialize(self):
        if self.model_path.exists():
            try:
                self.pipeline = joblib.load(self.model_path)
            except Exception:
                self._build_pipeline()
        else:
            self._build_pipeline()

    def _build_pipeline(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=10000,
                sublinear_tf=True,
                stop_words="english"
            )),
            ("clf", LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=42
            ))
        ])

    def fit(self, texts: list[str], labels: list[int]):
        """Fits the pipeline on texts and binary labels (0 = Real, 1 = Fake)."""
        self.pipeline.fit(texts, labels)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)

    def predict(self, text: str) -> BaselinePrediction:
        """Runs inference and extracts top n-gram predictive cues."""
        if not self.pipeline:
            raise ValueError("Classifier pipeline is not initialized.")

        cleaned = text.strip()
        probs = self.pipeline.predict_proba([cleaned])[0]
        real_prob = float(probs[0])
        fake_prob = float(probs[1])

        label = "FAKE" if fake_prob >= 0.50 else "REAL"
        confidence = max(real_prob, fake_prob)

        # Extract top feature weights for this text
        tfidf = self.pipeline.named_steps["tfidf"]
        clf = self.pipeline.named_steps["clf"]
        feature_names = np.array(tfidf.get_feature_names_out())
        coefs = clf.coef_[0]

        # Transform single document
        doc_vec = tfidf.transform([cleaned])
        nonzero_indices = doc_vec.nonzero()[1]

        cues = []
        for idx in nonzero_indices:
            term = feature_names[idx]
            weight = coefs[idx] * doc_vec[0, idx]
            direction = "FAVORS_FAKE" if weight > 0 else "FAVORS_REAL"
            cues.append({
                "term": str(term),
                "weight": float(round(weight, 4)),
                "direction": direction
            })

        # Sort by absolute weight magnitude
        cues.sort(key=lambda x: abs(x["weight"]), reverse=True)

        top_cues = cues[:5]
        explanation = (
            f"Baseline classifier evaluated stylistic lexical markers. "
            f"Predicted '{label}' with {confidence * 100:.1f}% probability based purely on vocabulary patterns, "
            f"without verifying real-world evidence."
        )

        return BaselinePrediction(
            label=label,
            fake_probability=round(fake_prob, 4),
            real_probability=round(real_prob, 4),
            confidence=round(confidence, 4),
            top_predictive_cues=top_cues,
            explanation=explanation
        )


baseline_classifier = BaselineTextClassifier()
