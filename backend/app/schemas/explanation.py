from pydantic import BaseModel, Field
from backend.app.schemas.verification import EvidenceGraph, AuditTrail
from backend.app.schemas.veracity import VeracityLabel


class CalibratedUncertainty(BaseModel):
    temperature_factor: float
    raw_confidence: float
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0)
    expected_calibration_error: float = Field(..., ge=0.0, le=1.0)
    uncertainty_level: str  # "LOW", "MODERATE", "HIGH"


class VerificationAuditReport(BaseModel):
    job_id: str
    target_claim: str
    verdict: VeracityLabel
    uncertainty: CalibratedUncertainty
    sufficiency_index: float
    audit_trail: AuditTrail
    evidence_graph: EvidenceGraph
    export_timestamp: str
