from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Any, Dict


class SyntheticMediaDetector(ABC):
    """Abstract interface for synthetic media and generative AI detection modules."""

    @abstractmethod
    def analyze(self, media_path: Path | str) -> dict[str, Any]:
        """Analyzes media artifact and returns probabilistic indicators and uncertainty bounds."""
        pass


class HeuristicFrequencySyntheticDetector(SyntheticMediaDetector):
    """Modular lightweight synthetic media detector analyzing frequency domain characteristics,
    color variance profiles, and gradient edge distributions.
    Emits continuous probabilities without fabricating claims of certainty."""

    def __init__(self):
        self.model_name = "HeuristicFrequencySyntheticDetector"
        self.version = "1.2.0"
        self.preprocessing = "RGB normalization, Laplacian gradient variance, saturation spread"

    def analyze(self, media_path: Path | str) -> dict[str, Any]:
        path = Path(media_path)
        if not path.exists():
            return {
                "model_name": self.model_name,
                "model_version": self.version,
                "preprocessing": self.preprocessing,
                "synthetic_probability": 0.0,
                "confidence": "LOW",
                "limitations": "Media file not found on disk.",
                "notes": ["Image file unavailable"],
            }

        notes = []

        try:
            with Image.open(path) as img:
                rgb = img.convert("RGB")
                arr = np.asarray(rgb, dtype=np.float32) / 255.0

                # Analyze frequency characteristics & color saturation distribution
                # Diffusion-generated images frequently exhibit characteristic high-saturation dispersion
                std_channels = np.std(arr, axis=(0, 1))
                mean_saturation = float(np.mean(std_channels))

                # Compute discrete laplacian variance (proxy for unnatural edge sharpness / ultra-smoothing)
                gray = np.mean(arr, axis=2)
                gy, gx = np.gradient(gray)
                edge_variance = float(np.var(gx) + np.var(gy))

                # Continuous probabilistic model
                # Base prior probability: 0.15 (conservative baseline prior for web media)
                p_synthetic = 0.15

                # Adjust based on color dispersion
                if mean_saturation > 0.28:
                    p_synthetic += 0.25
                elif mean_saturation < 0.10:
                    p_synthetic -= 0.05

                # Adjust based on unnatural edge smoothness
                if edge_variance < 0.005:
                    p_synthetic += 0.20
                    notes.append("Unusual high-frequency texture smoothing detected.")
                elif edge_variance > 0.035:
                    p_synthetic -= 0.10

                # Bound probability strictly in [0.05, 0.95] to prevent false overconfidence
                p_synthetic = float(round(max(0.05, min(0.95, p_synthetic)), 3))

                # Calibrated confidence rating
                if p_synthetic > 0.70 or p_synthetic < 0.30:
                    confidence = "MODERATE"
                else:
                    confidence = "LOW"

                limitations = (
                    "This is a probabilistic model signal with inherent uncertainty. "
                    "Social media re-encoding, heavy JPEG compression, or artistic filters can alter frequency statistics. "
                    "Does not provide binary or definitive proof of AI generation."
                )

                notes.append(
                    f"Probabilistic AI-generation indicator: P(synthetic) = {p_synthetic:.2f} (Confidence: {confidence}). "
                    f"Notice: Compression artifacts can alter texture statistics."
                )

                return {
                    "model_name": self.model_name,
                    "model_version": self.version,
                    "preprocessing": self.preprocessing,
                    "synthetic_probability": p_synthetic,
                    "confidence": confidence,
                    "limitations": limitations,
                    "notes": notes,
                }

        except Exception as exc:
            return {
                "model_name": self.model_name,
                "model_version": self.version,
                "preprocessing": self.preprocessing,
                "synthetic_probability": 0.0,
                "confidence": "LOW",
                "limitations": f"Inference failure: {str(exc)}",
                "notes": [f"Synthetic analysis error: {str(exc)}"],
            }


# Default detector instance
synthetic_detector = HeuristicFrequencySyntheticDetector()

