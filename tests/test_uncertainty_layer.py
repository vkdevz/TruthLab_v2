"""Unit tests for Uncertainty Estimation Layer (Commit 12).
"""

from backend.app.ml.explainability.uncertainty_layer import uncertainty_layer
from backend.app.schemas.explanation import CalibratedUncertainty


def test_high_uncertainty_when_insufficient_evidence():
    # Low confidence, near-zero evidence sufficiency -> Should yield HIGH uncertainty and is_actionable=False
    uncert = uncertainty_layer.estimate_uncertainty(
        raw_confidence=0.45,
        verdict_distribution={
            "SUPPORTED": 0.2,
            "CONTRADICTED": 0.2,
            "MISLEADING": 0.2,
            "OUTDATED": 0.2,
            "INSUFFICIENT_EVIDENCE": 0.2,
        },
        evidence_sufficiency=0.10,
        has_conflicting_evidence=True,
    )
    assert uncert.uncertainty_level == "HIGH"
    assert uncert.is_actionable is False
    assert uncert.epistemic_uncertainty > 0.50
    assert uncert.entropy > 0.80


def test_low_uncertainty_when_sufficient_evidence():
    # High confidence, high evidence sufficiency, consistent distribution -> LOW uncertainty
    uncert = uncertainty_layer.estimate_uncertainty(
        raw_confidence=0.95,
        verdict_distribution={
            "SUPPORTED": 0.95,
            "CONTRADICTED": 0.01,
            "MISLEADING": 0.02,
            "OUTDATED": 0.01,
            "INSUFFICIENT_EVIDENCE": 0.01,
        },
        evidence_sufficiency=2.50,
        has_conflicting_evidence=False,
    )
    assert uncert.uncertainty_level == "LOW"
    assert uncert.is_actionable is True
    assert uncert.uncertainty_score < 0.35
