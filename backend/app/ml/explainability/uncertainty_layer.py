"""Comprehensive Uncertainty Estimation Layer.

Disentangles verdict, confidence, epistemic uncertainty, aleatoric uncertainty,
and evidence sufficiency to prevent presenting high-uncertainty verdicts
as definitive factual truth.
"""

from __future__ import annotations

import numpy as np
from backend.app.schemas.explanation import CalibratedUncertainty
from backend.app.ml.explainability.calibration import confidence_calibrator


class UncertaintyLayer:
    """Computes multidimensional uncertainty metrics for verification decisions."""

    def __init__(self, temperature: float = 1.15):
        self.temperature = temperature

    def estimate_uncertainty(
        self,
        raw_confidence: float,
        verdict_distribution: dict[str, float] | None = None,
        evidence_sufficiency: float = 1.0,
        media_manipulation_score: float = 0.0,
        has_conflicting_evidence: bool = False,
    ) -> CalibratedUncertainty:
        # 1. Calibrated point confidence via temperature scaling
        base_calib = confidence_calibrator.calibrate(raw_confidence)
        calibrated_p = base_calib.calibrated_confidence

        # 2. Shannon Entropy over 5-class distribution
        if verdict_distribution and len(verdict_distribution) > 0:
            probs = np.array([max(1e-6, p) for p in verdict_distribution.values()])
            probs = probs / np.sum(probs)
            # Max entropy for 5 uniform classes is log2(5) ~= 2.3219
            raw_entropy = float(-np.sum(probs * np.log2(probs)))
            normalized_entropy = float(np.clip(raw_entropy / 2.3219, 0.0, 1.0))
        else:
            normalized_entropy = float(round(1.0 - calibrated_p, 3))

        # 3. Epistemic Uncertainty (knowledge deficit from lack of evidence or conflict)
        # Sufficiency threshold is 1.20; deficit scaled [0, 1]
        sufficiency_deficit = float(np.clip(1.0 - (evidence_sufficiency / 1.20), 0.0, 1.0))
        conflict_factor = 0.25 if has_conflicting_evidence else 0.0
        epistemic = float(np.clip(0.6 * sufficiency_deficit + 0.4 * normalized_entropy + conflict_factor, 0.0, 1.0))

        # 4. Aleatoric Uncertainty (sensor noise, media compression, visual ambiguity)
        aleatoric = float(np.clip(media_manipulation_score, 0.0, 1.0))

        # 5. Composite Uncertainty Score
        composite_uncertainty = float(round(max(epistemic, 1.0 - calibrated_p), 3))

        # 6. Categorical Level
        if composite_uncertainty <= 0.30:
            level = "LOW"
        elif composite_uncertainty <= 0.60:
            level = "MODERATE"
        else:
            level = "HIGH"

        # Actionability: high uncertainty forbids presenting claim as certain truth
        is_actionable = (level != "HIGH") and (evidence_sufficiency >= 0.80)

        return CalibratedUncertainty(
            temperature_factor=self.temperature,
            raw_confidence=round(raw_confidence, 3),
            calibrated_confidence=calibrated_p,
            expected_calibration_error=base_calib.expected_calibration_error,
            uncertainty_level=level,
            uncertainty_score=composite_uncertainty,
            epistemic_uncertainty=round(epistemic, 3),
            aleatoric_uncertainty=round(aleatoric, 3),
            evidence_sufficiency=round(evidence_sufficiency, 3),
            entropy=round(normalized_entropy, 3),
            is_actionable=is_actionable,
        )


uncertainty_layer = UncertaintyLayer()
