import pytest
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.media import ImageForensicIndicators
from backend.app.schemas.temporal import TemporalVerificationResult
from backend.app.schemas.veracity import VeracityLabel, StanceType
from backend.app.ml.fusion.cross_modal_alignment import cross_modal_alignment
from backend.app.ml.fusion.fusion_model import multimodal_fusion_model


def test_cross_modal_alignment():
    # Congruent caption and OCR
    score_congruent, notes_c = cross_modal_alignment.compute_alignment(
        claim_text="NASA rover lands on Mars surface",
        ocr_text="NASA Mars Rover Mission Live Landing Broadcast"
    )
    assert score_congruent >= 0.85

    # Cheapfake / Mismatched caption
    score_mismatched, notes_m = cross_modal_alignment.compute_alignment(
        claim_text="Violent riots break out in downtown capital city",
        ocr_text="Annual Summer Carnival and Parade Festival 2019"
    )
    assert score_mismatched < 0.70
    assert any("Cross-modal disparity" in n for n in notes_m)


def test_fusion_cheapfake_resolution():
    claim = AtomicClaim(
        id="c-cheapfake",
        raw_text="Violent riots break out in downtown city",
        canonical_claim="Violent riots break out in downtown city",
        checkworthy_score=0.90,
        is_checkworthy=True
    )
    # Evidence for riots is inconclusive or non-existent
    ev = EvidenceSnippet(
        id="e-cf",
        claim_id=claim.id,
        source_name="News Archive",
        source_url="https://example.com/carnival",
        domain="example.com",
        snippet_text="Citizens enjoyed peaceful annual carnival parade downtown.",
        retrieval_score=0.85,
        stance=StanceType.NEUTRAL,
        stance_probabilities={"SUPPORTS": 0.1, "REFUTES": 0.1, "NEUTRAL": 0.8}
    )
    # Genuine photo (not spliced), but OCR reveals it's a carnival
    img_forensics = ImageForensicIndicators(
        has_exif=True,
        c2pa_present=False,
        ela_max_error=0.10,
        is_ela_spliced=False,
        synthetic_probability=0.10,
        synthetic_confidence="LOW"
    )
    decision = multimodal_fusion_model.fuse(
        claim=claim,
        evidence_items=[ev],
        image_forensics=img_forensics,
        ocr_text="Annual Summer Carnival and Parade Festival 2019"
    )
    # Must resolve to MISLEADING rather than SUPPORTED
    assert decision.final_verdict == VeracityLabel.MISLEADING
    assert len(decision.fusion_rationale) > 0


def test_fusion_supported_resolution():
    claim = AtomicClaim(
        id="c-supp",
        raw_text="NASA's Webb telescope detected carbon dioxide on exoplanet WASP-39b",
        canonical_claim="NASA's Webb telescope detected carbon dioxide on exoplanet WASP-39b",
        checkworthy_score=0.95,
        is_checkworthy=True
    )
    ev = EvidenceSnippet(
        id="e-supp",
        claim_id=claim.id,
        source_name="NASA Press",
        source_url="https://nasa.gov/webb",
        domain="nasa.gov",
        snippet_text="NASA confirms James Webb Space Telescope detected atmospheric carbon dioxide on WASP-39b.",
        retrieval_score=0.92,
        stance=StanceType.SUPPORTS,
        stance_probabilities={"SUPPORTS": 0.95, "REFUTES": 0.02, "NEUTRAL": 0.03},
        is_claim_review=True
    )
    img_forensics = ImageForensicIndicators(
        has_exif=True,
        c2pa_present=True,
        synthetic_probability=0.12,
        synthetic_confidence="LOW"
    )
    decision = multimodal_fusion_model.fuse(
        claim=claim,
        evidence_items=[ev],
        image_forensics=img_forensics
    )
    assert decision.final_verdict == VeracityLabel.SUPPORTED
    assert decision.confidence >= 0.80
