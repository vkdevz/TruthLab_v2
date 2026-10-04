from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.schemas.claim import AtomicClaim
from backend.app.ml.claim.decomposer import claim_decomposer

router = APIRouter(prefix="/claims", tags=["Claim Intelligence"])


class ClaimDecomposeRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Input text, transcript, or OCR corpus to decompose into atomic claims")


class ClaimDecomposeResponse(BaseModel):
    total_claims: int
    checkworthy_count: int
    claims: list[AtomicClaim]


@router.post("/extract", response_model=ClaimDecomposeResponse)
async def extract_claims(payload: ClaimDecomposeRequest):
    try:
        claims = claim_decomposer.decompose(payload.text)
        checkworthy = [c for c in claims if c.is_checkworthy]
        return ClaimDecomposeResponse(
            total_claims=len(claims),
            checkworthy_count=len(checkworthy),
            claims=claims,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(exc)}")
