from pathlib import Path
from PIL import Image
import numpy as np


class SyntheticImageDetector:
    """Probabilistic AI-generated image analysis.
    Explicitly outputs continuous probabilities rather than absolute claims,
    and documents social media compression limitations."""

    def analyze(self, image_path: Path | str) -> dict[str, any]:
        path = Path(image_path)
        if not path.exists():
            return {
                "synthetic_probability": 0.0,
                "confidence": "LOW",
                "notes": ["Image file unavailable"]
            }

        notes = []

        try:
            with Image.open(path) as img:
                rgb = img.convert("RGB")
                arr = np.asarray(rgb, dtype=np.float32) / 255.0

                # Analyze frequency characteristics & color saturation distribution
                # Synthetic images from early/mid-tier diffusion models frequently exhibit
                # characteristic oversaturation and ultra-smooth gradient fields
                std_channels = np.std(arr, axis=(0, 1))
                mean_saturation = float(np.mean(std_channels))

                # Compute discrete laplacian variance (proxy for edge sharpness uniformity)
                gray = np.mean(arr, axis=2)
                # Simple discrete gradient
                gy, gx = np.gradient(gray)
                edge_variance = float(np.var(gx) + np.var(gy))

                # Continuous probabilistic model
                # Base prior probability: 0.15 (most web photos are natural)
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

                # Bound probability in [0.05, 0.95]
                p_synthetic = float(round(max(0.05, min(0.95, p_synthetic)), 3))

                # Calibrated confidence rating
                if p_synthetic > 0.70 or p_synthetic < 0.30:
                    confidence = "MODERATE"
                else:
                    confidence = "LOW"

                notes.append(
                    f"Probabilistic AI-generation indicator: P(synthetic) = {p_synthetic:.2f} (Confidence: {confidence}). "
                    f"Notice: Compression artifacts from messaging apps can alter texture statistics."
                )

                return {
                    "synthetic_probability": p_synthetic,
                    "confidence": confidence,
                    "notes": notes,
                }

        except Exception as exc:
            return {
                "synthetic_probability": 0.0,
                "confidence": "LOW",
                "notes": [f"Synthetic analysis error: {str(exc)}"],
            }


synthetic_detector = SyntheticImageDetector()
