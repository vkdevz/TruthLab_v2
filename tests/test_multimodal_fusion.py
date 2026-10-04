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


def test_fusion_textual_refutation_dominates_weak_media_signal():
    """Authoritative external evidence refuting a claim dominates media signals."""
    claim = AtomicClaim(
        id="c-refute",
        raw_text="The Eiffel Tower collapsed in a fire today",
        canonical_claim="The Eiffel Tower collapsed in a fire today",
        checkworthy_score=0.95,
        is_checkworthy=True
    )
    ev = EvidenceSnippet(
        id="e-refute",
        claim_id=claim.id,
        source_name="Reuters Fact Check",
        source_url="https://reuters.com/factcheck/eiffel-tower",
        domain="reuters.com",
        snippet_text="No, the Eiffel Tower has not collapsed or suffered a fire. Paris authorities confirm the landmark is open and undamaged.",
        retrieval_score=0.96,
        stance=StanceType.REFUTES,
        stance_probabilities={"SUPPORTS": 0.01, "REFUTES": 0.98, "NEUTRAL": 0.01},
        is_claim_review=True
    )
    # Even if image has EXIF and low synthetic probability, the textual claim is false
    img_forensics = ImageForensicIndicators(
        has_exif=True,
        c2pa_present=False,
        synthetic_probability=0.08,
        synthetic_confidence="LOW"
    )
    decision = multimodal_fusion_model.fuse(
        claim=claim,
        evidence_items=[ev],
        image_forensics=img_forensics
    )
    assert decision.final_verdict == VeracityLabel.CONTRADICTED
    assert any("refut" in r.lower() or "contradict" in r.lower() for r in decision.fusion_rationale)


def test_fusion_temporal_penalty_outdated():
    """Historical event recycled as breaking news resolves to OUTDATED."""
    claim = AtomicClaim(
        id="c-outdated",
        raw_text="Massive earthquake hits coastal Japan right now",
        canonical_claim="Massive earthquake hits coastal Japan right now",
        checkworthy_score=0.92,
        is_checkworthy=True
    )
    ev = EvidenceSnippet(
        id="e-hist",
        claim_id=claim.id,
        source_name="Kyodo News Archive",
        source_url="https://kyodo.jp/archive/2011",
        domain="kyodo.jp",
        snippet_text="In March 2011, a magnitude 9.0 earthquake struck off the coast of Tohoku Japan.",
        retrieval_score=0.88,
        stance=StanceType.SUPPORTS,
        stance_probabilities={"SUPPORTS": 0.85, "REFUTES": 0.05, "NEUTRAL": 0.10}
    )
    temporal_res = TemporalVerificationResult(
        is_temporal_claim=True,
        extracted_claim_date="2026-10-04",
        source_published_date="2011-03-11",
        event_date="2011-03-11",
        temporal_gap_days=5686,
        temporal_consistency_score=0.20,
        temporal_status="OUTDATED",
        reason="Claim refers to 2011 event as if occurring today."
    )
    decision = multimodal_fusion_model.fuse(
        claim=claim,
        evidence_items=[ev],
        temporal_result=temporal_res
    )
    assert decision.final_verdict == VeracityLabel.OUTDATED
    assert any("recycl" in r.lower() or "outdated" in r.lower() for r in decision.fusion_rationale)


def test_fusion_insufficient_evidence():
    """Claims lacking reliable corroboration resolve to INSUFFICIENT_EVIDENCE."""
    claim = AtomicClaim(
        id="c-unverifiable",
        raw_text="A secret underground city was discovered beneath Antarctica yesterday",
        canonical_claim="A secret underground city was discovered beneath Antarctica yesterday",
        checkworthy_score=0.60,
        is_checkworthy=True
    )
    decision = multimodal_fusion_model.fuse(
        claim=claim,
        evidence_items=[]
    )
    assert decision.final_verdict == VeracityLabel.INSUFFICIENT_EVIDENCE
    assert decision.confidence < 0.50


def test_fusion_serialization():
    """Verify FusionDecision can be cleanly dumped and serialized into response schemas."""
    from datetime import datetime, timezone
    from backend.app.schemas.verification import (
        FullVerificationResponse,
        ClaimVerificationResult,
        AuditTrail,
        EvidenceGraph
    )
    from backend.app.schemas.veracity import ModalityType

    claim = AtomicClaim(
        id="c-ser",
        raw_text="Sample claim for serialization test",
        canonical_claim="Sample claim for serialization test",
        checkworthy_score=0.75,
        is_checkworthy=True
    )
    decision = multimodal_fusion_model.fuse(claim=claim, evidence_items=[])
    data = decision.model_dump()
    assert "final_verdict" in data
    assert "fusion_rationale" in data
    assert "dimension_scores" in data

    resp = FullVerificationResponse(
        job_id="test-job-id",
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        input_modality=ModalityType.IMAGE,
        overall_veracity=decision.final_verdict,
        overall_confidence=decision.confidence,
        claims_verified=[
            ClaimVerificationResult(
                claim=claim,
                veracity=decision.final_verdict,
                confidence=decision.confidence,
                evidence_sufficiency_score=0.0,
                is_temporal_mismatch=False,
                evidence_items=[],
                audit=AuditTrail(
                    summary="Test audit summary",
                    limitations=[]
                )
            )
        ],
        ocr_text="Sample OCR extracted text",
        evidence_graph=EvidenceGraph(nodes=[], edges=[]),
        executive_summary="Sample executive summary",
        system_limitations=["Signal uncertainty"]
    )
    resp_dict = resp.model_dump()
    assert resp_dict["ocr_text"] == "Sample OCR extracted text"
    assert resp_dict["overall_veracity"] == decision.final_verdict.value

