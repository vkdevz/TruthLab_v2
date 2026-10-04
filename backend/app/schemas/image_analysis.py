from pydantic import BaseModel, Field
from backend.app.schemas.media import ImageForensicIndicators
from backend.app.schemas.verification import ClaimVerificationResult


class ImageAnalysisResponse(BaseModel):
    filename: str
    ocr_extracted_text: str | None = None
    has_text_content: bool = False
    forensics: ImageForensicIndicators
    verified_claims: list[ClaimVerificationResult] = Field(default_factory=list)
    overall_assessment: str
