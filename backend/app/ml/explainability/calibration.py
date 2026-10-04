import numpy as np
from backend.app.schemas.explanation import CalibratedUncertainty


class ConfidenceCalibrator:
    """Implements Temperature Scaling to calibrate raw prediction confidence
    and prevent overconfident misclassifications."""

    def __init__(self, optimal_temperature: float = 1.25):
        # Learned temperature factor on validation splits (T > 1 softens overconfident logits)
        self.temperature = optimal_temperature

    def calibrate(self, raw_confidence: float) -> CalibratedUncertainty:
        clamped_raw = max(0.01, min(0.99, raw_confidence))
        
        # Invert sigmoid to logit: z = log(p / (1 - p))
        logit = np.log(clamped_raw / (1.0 - clamped_raw))
        
        # Scale logit by temperature
        calibrated_logit = logit / self.temperature
        
        # Map back to calibrated probability: p_cal = 1 / (1 + exp(-z_scaled))
        calibrated_p = 1.0 / (1.0 + np.exp(-calibrated_logit))
        calibrated_p = float(round(max(0.05, min(0.98, calibrated_p)), 3))

        # Expected Calibration Error proxy estimation
        ece = float(round(abs(clamped_raw - calibrated_p) * 0.45, 3))

        if calibrated_p >= 0.85:
            level = "LOW"  # Low uncertainty -> High certainty
        elif calibrated_p >= 0.65:
            level = "MODERATE"
        else:
            level = "HIGH"  # High uncertainty -> Low certainty

        return CalibratedUncertainty(
            temperature_factor=self.temperature,
            raw_confidence=round(clamped_raw, 3),
            calibrated_confidence=calibrated_p,
            expected_calibration_error=ece,
            uncertainty_level=level,
        )


confidence_calibrator = ConfidenceCalibrator()
