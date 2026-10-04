from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import Any
from backend.app.schemas.verification import FullVerificationResponse, ClaimVerificationResult
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.job_manager import job_manager
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.services.retrieval.web_retriever import web_retriever
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.nli.veracity_scorer import veracity_scorer

router = APIRouter(tags=["Evidence-Grounded Verification Engine"])


class VerifyTextRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=25000, description="Raw factual text, claim, or article body to verify")


class VerifyUrlRequest(BaseModel):
    url: str = Field(..., description="Target web page/article URL to verify safely against Anti-SSRF constraints")


class VerifyClaimRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Factual claim or paragraph to verify against external evidence")


class VerifyClaimResponse(BaseModel):
    total_claims_processed: int
    results: list[ClaimVerificationResult]


# Phase 1 Core Workflow Endpoints
@router.post("/verify/text", response_model=FullVerificationResponse, summary="Verify raw text or claim end-to-end")
async def verify_text_endpoint(payload: VerifyTextRequest):
    """End-to-end pipeline:
    Text -> Normalization -> Claim Decomposition -> Evidence Retrieval -> Ranking -> NLI -> 5-Class Verdict -> Explanation
    """
    return await pipeline_service.verify_text(payload.text)


@router.post("/verify/url", response_model=FullVerificationResponse, summary="Verify article URL end-to-end")
async def verify_url_endpoint(payload: VerifyUrlRequest):
    """End-to-end pipeline with strict Anti-SSRF protection:
    URL -> SSRF Validation -> Safe Ingestion -> Article Extraction -> Claim Decomposition -> Evidence -> Verdict
    """
    return await pipeline_service.verify_url(payload.url)


@router.post("/verify/image", response_model=FullVerificationResponse, summary="Verify image / screenshot / meme end-to-end")
async def verify_image_endpoint(file: UploadFile = File(...)):
    """End-to-end image verification pipeline:
    Image -> Validation -> OCR & Forensics -> Claim Extraction -> Evidence Retrieval -> Verdict -> Graph
    """
    return await pipeline_service.verify_image(file)


@router.post("/verify/video", response_model=FullVerificationResponse, summary="Verify video clip end-to-end")
async def verify_video_endpoint(file: UploadFile = File(...)):
    """End-to-end video verification pipeline:
    Video -> Validation -> Probe & Keyframe OCR & ASR -> Claim Extraction -> Evidence -> Verdict -> Graph
    """
    return await pipeline_service.verify_video(file)



@router.get("/verification/{job_id}", summary="Retrieve verification record by ID")
async def get_verification_by_id(job_id: str):
    """Retrieves full persistent verification record and explanation graph by job ID."""
    job_record = await job_manager.get_job_status(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Verification job '{job_id}' not found.")
    return job_record


@router.get("/verify/{job_id}", summary="Alias to retrieve verification record by ID")
async def get_verify_by_id_alias(job_id: str):
    return await get_verification_by_id(job_id)


# Existing endpoint preserved for backward compatibility
@router.post("/verify/claim", response_model=VerifyClaimResponse, summary="Legacy claim verification endpoint")
async def verify_claim_endpoint(payload: VerifyClaimRequest):
    try:
        claims = claim_decomposer.decompose(payload.text)
        if not claims:
            raise HTTPException(status_code=400, detail="No verifiable statements found in provided text.")

        verification_results: list[ClaimVerificationResult] = []

        for c in claims:
            raw_evidence = await web_retriever.retrieve_evidence(
                claim_id=c.id,
                claim_text=c.canonical_claim,
                search_queries=c.search_queries
            )
            reranked_evidence = evidence_reranker.rerank(c.canonical_claim, raw_evidence)
            stanced_evidence = stance_classifier.evaluate_evidence_stances(c.canonical_claim, reranked_evidence)
            result = veracity_scorer.score_claim(c, stanced_evidence)
            verification_results.append(result)

        return VerifyClaimResponse(
            total_claims_processed=len(claims),
            results=verification_results,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(exc)}")
