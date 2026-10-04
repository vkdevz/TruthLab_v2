from pydantic import BaseModel, Field
from backend.app.schemas.media import VideoForensicIndicators
from backend.app.schemas.verification import ClaimVerificationResult


class VideoAnalysisResponse(BaseModel):
    filename: str
    duration_seconds: float
    transcript_text: str | None = None
    extracted_keyframes_count: int = 0
    overlay_ocr_text: str | None = None
    unified_corpus: str = Field(..., description="Combined transcript and visual OCR text")
    forensics: VideoForensicIndicators
    verified_claims: list[ClaimVerificationResult] = Field(default_factory=list)
    overall_assessment: str
