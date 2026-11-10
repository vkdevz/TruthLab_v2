from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.services.storage import storage_service
from backend.app.ml.image.ocr_engine import ocr_engine
from backend.app.ml.image.metadata_forensics import metadata_forensics
from backend.app.ml.image.ela_forensics import ela_forensics
from backend.app.ml.image.synthetic_detector import synthetic_detector
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.services.retrieval.web_retriever import web_retriever
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.nli.veracity_scorer import veracity_scorer
from backend.app.schemas.image_analysis import ImageAnalysisResponse
from backend.app.schemas.media import ImageForensicIndicators
from backend.app.schemas.verification import ClaimVerificationResult

router = APIRouter(prefix="/image", tags=["Image Intelligence"])


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    # 1. Save uploaded image to safe local storage
    saved_path = await storage_service.save_upload_file(file, is_video=False)

    try:
        # 2. Extract OCR Text
        ocr_text = ocr_engine.extract_text(saved_path)
        has_text = bool(ocr_text and len(ocr_text.strip()) > 5)

        # 3. Perform Forensics
        meta_res = metadata_forensics.analyze(saved_path)
        ela_res = ela_forensics.analyze(saved_path)
        synth_res = synthetic_detector.analyze(saved_path)

        all_notes = meta_res["notes"] + ela_res["notes"] + synth_res["notes"]

        forensic_indicators = ImageForensicIndicators(
            has_exif=meta_res["has_exif"],
            software_tag=meta_res["software_tag"],
            c2pa_present=meta_res["c2pa_present"],
            ela_max_error=ela_res["ela_max_error"],
            is_ela_spliced=ela_res["is_ela_spliced"],
            synthetic_probability=synth_res["synthetic_probability"],
            synthetic_confidence=synth_res["confidence"],
            forensic_notes=all_notes,
        )

        # 4. If text was extracted, verify the factual claims embedded in the image
        verified_claims: list[ClaimVerificationResult] = []
        if has_text:
            extracted_claims = claim_decomposer.decompose(ocr_text)
            for c in extracted_claims:
                raw_ev = await web_retriever.retrieve_evidence(c.id, c.canonical_claim, c.search_queries)
                reranked_ev = evidence_reranker.rerank(c.canonical_claim, raw_ev)
                stanced_ev = stance_classifier.evaluate_evidence_stances(c.canonical_claim, reranked_ev)
                result = veracity_scorer.score_claim(
                    claim=c,
                    evidence_items=stanced_ev,
                    image_forensics=forensic_indicators,
                    ocr_text=ocr_text,
                )
                verified_claims.append(result)

        # 5. Formulate summary
        if forensic_indicators.is_ela_spliced:
            assessment = "Visual tampering / splicing indicators detected. Exercise caution."
        elif forensic_indicators.synthetic_probability > 0.75:
            assessment = "Elevated indicators of probabilistic AI generation."
        elif has_text and verified_claims:
            assessment = f"Extracted {len(verified_claims)} embedded claim(s) from image for empirical verification."
        else:
            assessment = "Visual forensics show normal texture characteristics with no obvious tampering detected."

        return ImageAnalysisResponse(
            filename=file.filename or saved_path.name,
            ocr_extracted_text=ocr_text if has_text else None,
            has_text_content=has_text,
            forensics=forensic_indicators,
            verified_claims=verified_claims,
            overall_assessment=assessment,
        )

    finally:
        storage_service.cleanup_file(saved_path)
