from datetime import datetime
from pydantic import BaseModel, Field


class TemporalVerificationResult(BaseModel):
    claim_anchor: str | None = None
    claim_date: datetime | None = None
    evidence_date: datetime | None = None
    delta_days: int | None = None
    is_outdated: bool = False
    is_anachronistic: bool = False
    present_framing_detected: bool = False
    location_match_status: str = "CONSISTENT"  # CONSISTENT, MISMATCH, UNKNOWN
    temporal_notes: list[str] = Field(default_factory=list)
