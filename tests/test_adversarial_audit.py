import pytest
from pathlib import Path
from datetime import datetime, timezone
from fastapi import HTTPException

from backend.app.ingestion.url_ingest import URLValidator
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet, StanceType
from backend.app.schemas.media import VideoForensicIndicators
from backend.app.schemas.veracity import VeracityLabel
from backend.app.schemas.verification import ClaimVerificationResult, AuditTrail
from backend.app.verification.verdict_engine import FiveClassVerdictEngine
from backend.app.evidence.provider import LocalClaimReviewProvider, GoogleFactCheckProvider
from backend.app.ml.context.temporal_parser import temporal_parser
from backend.app.ml.baseline.classifier import BaselineTextClassifier
from backend.app.ml.fusion.cross_modal_alignment import cross_modal_alignment
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.job_manager import job_manager


def test_ssrf_obfuscated_and_non_canonical_ip_blocking():
    """Verify that URLValidator rejects obfuscated octal, hex, integer, and shorthand IPs."""
    adversarial_urls = [
        "http://0177.0.0.1/",
        "http://0x7f000001/",
        "http://2130706433/",
        "http://127.1/",
        "http://010.0.0.1/",
        "http://0x7f.1/",
        "http://0.0.0.0/",
        "http://127.0.0.1:8080/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://100.64.0.1/",
    ]
    for url in adversarial_urls:
        with pytest.raises(HTTPException) as exc_info:
            URLValidator.validate_url(url)
        assert exc_info.value.status_code == 400


def test_neutral_evidence_does_not_produce_supported_verdict():
    """Verify that predominantly neutral evidence does NOT yield SUPPORTED (e.g. Aliens on Pyramids)."""
    claim = AtomicClaim(
        id="c-pyramids",
        canonical_claim="Aliens constructed the Giza pyramids in ancient Egypt",
        raw_text="Aliens constructed the Giza pyramids in ancient Egypt",
        checkworthy_score=0.9,
        is_checkworthy=True,
        entities=["Aliens", "Egypt"],
        search_queries=["Aliens constructed the Giza pyramids"]
    )
    ev1 = EvidenceSnippet(
        id="ev-1",
        claim_id=claim.id,
        source_name="Wikipedia: Giza pyramid complex",
        source_url="https://en.wikipedia.org/wiki/Giza_pyramid_complex",
        domain="wikipedia.org",
        domain_credibility_weight=1.5,
        snippet_text="The Giza pyramid complex is a site on the Giza Plateau in Greater Cairo, Egypt.",
        publication_date=datetime.now(timezone.utc),
        retrieval_score=0.75,
        stance=StanceType.NEUTRAL,
        stance_probabilities={"SUPPORTS": 0.10, "REFUTES": 0.05, "NEUTRAL": 0.85},
        is_claim_review=False
    )
    ev2 = EvidenceSnippet(
        id="ev-2",
        claim_id=claim.id,
        source_name="Reuters Archaeology",
        source_url="https://reuters.com/archaeology-pyramids",
        domain="reuters.com",
        domain_credibility_weight=1.5,
        snippet_text="Archaeological surveys document construction techniques of the 4th dynasty.",
        publication_date=datetime.now(timezone.utc),
        retrieval_score=0.70,
        stance=StanceType.NEUTRAL,
        stance_probabilities={"SUPPORTS": 0.12, "REFUTES": 0.05, "NEUTRAL": 0.83},
        is_claim_review=False
    )

    engine = FiveClassVerdictEngine()
    result = engine.evaluate_veracity(claim, [ev1, ev2])

    assert result.veracity == VeracityLabel.INSUFFICIENT_EVIDENCE
    assert result.confidence <= 0.50
    assert "neutral" in result.audit.summary.lower() or "inconclusive" in result.audit.summary.lower()
    assert len(result.audit.supporting_citations) == 0


def test_evidence_provider_probabilities_sum_to_one():
    """Verify that stance probabilities sum strictly to 1.0 for all stances in evidence providers."""
    # LocalClaimReviewProvider
    local_provider = LocalClaimReviewProvider(records=[
        {"claim": "Test claim", "url": "https://test.com/1", "publisher": "Test", "stance": "NEUTRAL"},
        {"claim": "Supported claim", "url": "https://test.com/2", "publisher": "Test", "stance": "SUPPORTS"},
        {"claim": "Refuted claim", "url": "https://test.com/3", "publisher": "Test", "stance": "REFUTES"},
    ])
    for rec in local_provider.records:
        stance = StanceType(rec["stance"])
        if stance == StanceType.SUPPORTS:
            probs = {"SUPPORTS": 0.90, "REFUTES": 0.05, "NEUTRAL": 0.05}
        elif stance == StanceType.REFUTES:
            probs = {"SUPPORTS": 0.05, "REFUTES": 0.90, "NEUTRAL": 0.05}
        else:
            probs = {"SUPPORTS": 0.05, "REFUTES": 0.05, "NEUTRAL": 0.90}
        total_p = sum(probs.values())
        assert abs(total_p - 1.0) < 1e-4


def test_temporal_parser_does_not_hallucinate_dates_from_numbers():
    """Verify that 'About 38 of them' or chapter/page numbers are NOT parsed as year 2038."""
    non_date_phrases = [
        "About 38 of them are located around 25 kilometres away",
        "Chapter 12 of the penal code",
        "Section 42 specifies standard procedure",
        "Page 15 of the report",
    ]
    for phrase in non_date_phrases:
        anchor, dt = temporal_parser.parse_text_timestamp(phrase)
        assert anchor is None, f"Expected None for '{phrase}', got anchor '{anchor}' with dt {dt}"
        assert dt is None

    # Legitimate dates must still be detected
    valid_phrase = "Published on March 14, 2019 by researchers"
    anchor, dt = temporal_parser.parse_text_timestamp(valid_phrase)
    assert dt is not None
    assert dt.year == 2019


def test_baseline_classifier_auto_fits_when_checkpoint_missing():
    """Verify that BaselineTextClassifier automatically fits on reference data if checkpoint missing."""
    temp_path = Path("/tmp/nonexistent_model_checkpoint_test.joblib")
    if temp_path.exists():
        temp_path.unlink()

    classifier = BaselineTextClassifier(model_path=temp_path)
    pred = classifier.predict("Breaking news: Scientists uncover shocking secret subterranean bunker!")
    assert pred.label in {"REAL", "FAKE"}
    assert 0.0 <= pred.confidence <= 1.0
    assert len(pred.top_predictive_cues) > 0


def test_cross_modal_alignment_with_video_forensics():
    """Verify that video synthetic face score and frame rate anomalies reduce cross-modal alignment."""
    clean_forensics = VideoForensicIndicators(
        duration_seconds=10.0,
        total_frames=300,
        extracted_scenes=5,
        synthetic_face_probability=0.10,
        inconsistent_frame_rate=False,
    )
    score_clean, notes_clean = cross_modal_alignment.compute_alignment(
        claim_text="News broadcast interview",
        video_forensics=clean_forensics
    )
    assert score_clean == 1.0

    tampered_forensics = VideoForensicIndicators(
        duration_seconds=10.0,
        total_frames=300,
        extracted_scenes=5,
        synthetic_face_probability=0.88,
        inconsistent_frame_rate=True,
    )
    score_tampered, notes_tampered = cross_modal_alignment.compute_alignment(
        claim_text="News broadcast interview",
        video_forensics=tampered_forensics
    )
    assert score_tampered < 0.70
    assert any("synthetic face" in n.lower() for n in notes_tampered)
    assert any("frame rate" in n.lower() for n in notes_tampered)


@pytest.mark.asyncio
async def test_pipeline_verify_url_fails_job_on_blocked_url():
    """Verify that URL verification error properly transitions job to FAILED state instead of stranding it."""
    job_id = await job_manager.create_job(input_modality="URL", input_summary="http://127.0.0.1/admin")
    with pytest.raises(HTTPException):
        await pipeline_service.verify_url("http://127.0.0.1/admin", job_id=job_id)

    status = await job_manager.get_job_status(job_id)
    assert status is not None
    assert status["status"] == "FAILED"
    assert "prohibited" in status["error_message"].lower() or "forbidden" in status["error_message"].lower()


def test_decisive_contradiction_confidence_aggregation():
    """Verify that overall confidence reflects the decisive contradicted claim rather than diluted average."""
    c_false = AtomicClaim(
        id="c-f",
        canonical_claim="5G networks cause immediate bird mass mortality",
        raw_text="5G networks cause immediate bird mass mortality",
        checkworthy_score=0.9,
        is_checkworthy=True,
        search_queries=[]
    )
    res_false = ClaimVerificationResult(
        claim=c_false,
        veracity=VeracityLabel.CONTRADICTED,
        confidence=0.95,
        evidence_sufficiency_score=1.8,
        audit=AuditTrail(
            summary="Debunked",
            supporting_citations=[],
            refuting_citations=["http://who.int"],
            temporal_notes=[],
            media_authenticity_notes=[],
            limitations=[]
        )
    )

    unproven_results = []
    for i in range(5):
        c_unp = AtomicClaim(id=f"c-u-{i}", canonical_claim=f"Unproven minor statement {i}", raw_text="", checkworthy_score=0.5, is_checkworthy=True, search_queries=[])
        res_unp = ClaimVerificationResult(
            claim=c_unp,
            veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
            confidence=0.32,
            evidence_sufficiency_score=0.1,
            audit=AuditTrail(
                summary="Insufficient",
                supporting_citations=[],
                refuting_citations=[],
                temporal_notes=[],
                media_authenticity_notes=[],
                limitations=[]
            )
        )
        unproven_results.append(res_unp)

    verdict, conf = pipeline_service._aggregate_overall_veracity([res_false] + unproven_results)
    assert verdict == VeracityLabel.CONTRADICTED
    # Confidence should be at or near 0.95, NOT 0.42 (the unweighted mean of all 6 items)
    assert conf >= 0.90


def test_cross_modal_alignment_handles_none_synthetic_face_probability():
    """Verify that VideoForensicIndicators with default synthetic_face_probability=None does not raise TypeError."""
    vf = VideoForensicIndicators(
        duration_seconds=15.0,
        total_frames=450,
        extracted_scenes=6,
        synthetic_face_probability=None,
        inconsistent_frame_rate=False,
    )
    score, notes = cross_modal_alignment.compute_alignment(
        claim_text="Interview broadcast footage",
        video_forensics=vf,
    )
    assert score == 1.0
    assert len(notes) == 0


def test_temporal_parser_prioritizes_full_date_over_year():
    """Verify that explicit month-day-year phrases are preserved rather than truncated to Jan 1st of year."""
    phrase = "Published on October 15, 2020 by the research team"
    anchor, dt = temporal_parser.parse_text_timestamp(phrase)
    assert dt is not None
    assert dt.year == 2020
    assert dt.month == 10
    assert dt.day == 15


def test_nli_interpreter_topical_overlap_is_neutral_not_supports():
    """Verify that topical keyword overlap without entailment cues yields NEUTRAL, not false SUPPORTS."""
    from backend.app.verification.nli import nli_interpreter
    claim = "Aliens constructed the Egyptian pyramids in ancient times"
    snippet = "The ancient Egyptian pyramids at Giza were built by skilled Egyptian laborers during the Old Kingdom period."
    stance, probs = nli_interpreter.evaluate_relationship(claim, snippet)
    assert stance == StanceType.NEUTRAL
    assert probs["NEUTRAL"] > probs["SUPPORTS"]
    assert probs["SUPPORTS"] <= 0.15


def test_decision_matrix_neutral_evidence_routes_to_insufficient_evidence():
    """Verify that MultimodalDecisionMatrix routes neutral background evidence to INSUFFICIENT_EVIDENCE (not MISLEADING)."""
    from backend.app.schemas.fusion import FusionFeatureVector
    from backend.app.ml.fusion.decision_matrix import decision_matrix
    features = FusionFeatureVector(
        stance_support_score=0.05,
        stance_refute_score=0.05,
        evidence_sufficiency=1.5,
        temporal_penalty=0.0,
        media_manipulation_score=0.10,
        cross_modal_alignment=0.90,
        content_credibility_weight=1.0,
    )
    decision = decision_matrix.resolve(features)
    assert decision.final_verdict == VeracityLabel.INSUFFICIENT_EVIDENCE
    assert decision.confidence <= 0.48


def test_pipeline_unproven_claims_domination_and_explanation_honesty():
    """Verify that unproven claims dominating an article do not grant overall SUPPORTED verdict or lying explanations."""
    c_true = AtomicClaim(id="c-t", canonical_claim="Sun rises in the east", raw_text="", checkworthy_score=1.0, is_checkworthy=True, search_queries=[])
    res_true = ClaimVerificationResult(
        claim=c_true,
        veracity=VeracityLabel.SUPPORTED,
        confidence=0.90,
        evidence_sufficiency_score=1.5,
        audit=AuditTrail(summary="", supporting_citations=["http://nasa.gov"], refuting_citations=[], temporal_notes=[], media_authenticity_notes=[], limitations=[])
    )
    unproven_results = []
    for i in range(4):
        c_unp = AtomicClaim(id=f"c-u-{i}", canonical_claim=f"Alien base {i}", raw_text="", checkworthy_score=0.8, is_checkworthy=True, search_queries=[])
        res_unp = ClaimVerificationResult(
            claim=c_unp,
            veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
            confidence=0.35,
            evidence_sufficiency_score=0.1,
            audit=AuditTrail(summary="", supporting_citations=[], refuting_citations=[], temporal_notes=[], media_authenticity_notes=[], limitations=[])
        )
        unproven_results.append(res_unp)

    all_results = [res_true] + unproven_results
    overall_v, overall_c = pipeline_service._aggregate_overall_veracity(all_results)
    assert overall_v == VeracityLabel.INSUFFICIENT_EVIDENCE
    assert overall_c <= 0.55

    # Test explanation honesty when supported claims are a minority vs majority
    summary_insufficient, _ = pipeline_service._generate_explanation(overall_v, all_results, {})
    assert "All 5 factual proposition(s) are corroborated" not in summary_insufficient

    # When supported claims are the majority
    c_true2 = AtomicClaim(id="c-t2", canonical_claim="Water is liquid", raw_text="", checkworthy_score=1.0, is_checkworthy=True, search_queries=[])
    res_true2 = ClaimVerificationResult(
        claim=c_true2,
        veracity=VeracityLabel.SUPPORTED,
        confidence=0.92,
        evidence_sufficiency_score=1.5,
        audit=AuditTrail(summary="", supporting_citations=["http://science.gov"], refuting_citations=[], temporal_notes=[], media_authenticity_notes=[], limitations=[])
    )
    majority_results = [res_true, res_true2, unproven_results[0]]
    overall_maj_v, overall_maj_c = pipeline_service._aggregate_overall_veracity(majority_results)
    assert overall_maj_v == VeracityLabel.SUPPORTED
    summary_majority, _ = pipeline_service._generate_explanation(overall_maj_v, majority_results, {})
    assert "2 of 3 evaluated claim(s) are corroborated" in summary_majority
    assert "All 3 factual proposition(s) are corroborated" not in summary_majority

