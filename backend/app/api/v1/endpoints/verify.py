from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.services.retrieval.web_retriever import web_retriever
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.nli.veracity_scorer import veracity_scorer
from backend.app.schemas.verification import ClaimVerificationResult

router = APIRouter(prefix="/verify", tags=["Evidence-Grounded Verification Engine"])


class VerifyClaimRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Factual claim or paragraph to verify against external evidence")


class VerifyClaimResponse(BaseModel):
    total_claims_processed: int
    results: list[ClaimVerificationResult]


@router.post("/claim", response_model=VerifyClaimResponse)
async def verify_claim_endpoint(payload: VerifyClaimRequest):
    try:
        claims = claim_decomposer.decompose(payload.text)
        if not claims:
            raise HTTPException(status_code=400, detail="No verifiable statements found in provided text.")

        verification_results: list[ClaimVerificationResult] = []

        for c in claims:
            # 1. Retrieve evidence
            raw_evidence = await web_retriever.retrieve_evidence(
                claim_id=c.id,
                claim_text=c.canonical_claim,
                search_queries=c.search_queries
            )
            # 2. Rerank evidence
            reranked_evidence = evidence_reranker.rerank(c.canonical_claim, raw_evidence)
            # 3. Classify stances
            stanced_evidence = stance_classifier.evaluate_evidence_stances(c.canonical_claim, reranked_evidence)
            # 4. Score veracity
            result = veracity_scorer.score_claim(c, stanced_evidence)
            verification_results.append(result)

        return VerifyClaimResponse(
            total_claims_processed=len(claims),
            results=verification_results,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(exc)}")
