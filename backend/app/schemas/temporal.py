from datetime import datetime
from pydantic import BaseModel, Field


class TemporalVerificationResult(BaseModel):
    temporal_status: str = Field(
        default="UNKNOWN",
        description="Temporal category: CURRENT, HISTORICAL, OUTDATED, or UNKNOWN"
    )
    claim_anchor: str | None = None
    claim_date: datetime | None = None
    event_date: datetime | None = None
    source_date: datetime | None = None
    evidence_date: datetime | None = None
    reference_date: datetime | None = None
    delta_days: int | None = None
    is_outdated: bool = False
    is_anachronistic: bool = False
    present_framing_detected: bool = False
    reason: str | None = None
    location_match_status: str = "UNKNOWN"  # CONSISTENT, MISMATCH, UNKNOWN
    temporal_notes: list[str] = Field(default_factory=list)

