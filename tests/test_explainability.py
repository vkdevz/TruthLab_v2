import pytest
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.verification import AuditTrail
from backend.app.schemas.veracity import VeracityLabel, StanceType
from backend.app.ml.explainability.calibration import confidence_calibrator
from backend.app.ml.explainability.sufficiency import evidence_sufficiency_metric
from backend.app.ml.explainability.audit_generator import audit_report_generator


def test_confidence_calibrator():
    res = confidence_calibrator.calibrate(0.99)
    assert res.temperature_factor == 1.25
    assert res.raw_confidence == 0.99
    # Softened logit should yield lower calibrated confidence
    assert res.calibrated_confidence < 0.99
    assert res.uncertainty_level in {"LOW", "MODERATE", "HIGH"}
    assert res.expected_calibration_error >= 0.0


def test_evidence_sufficiency_metric():
    claim_id = "c-test-suff"
    ev1 = EvidenceSnippet(
        id="e-1",
        claim_id=claim_id,
        source_name="Reuters",
        source_url="https://reuters.com/1",
        domain="reuters.com",
        domain_credibility_weight=1.6,
        snippet_text="Text 1",
        retrieval_score=0.90,
        stance=StanceType.SUPPORTS
    )
    ev2 = EvidenceSnippet(
        id="e-2",
        claim_id=claim_id,
        source_name="BBC",
        source_url="https://bbc.com/2",
        domain="bbc.com",
        domain_credibility_weight=1.5,
        snippet_text="Text 2",
        retrieval_score=0.85,
        stance=StanceType.SUPPORTS,
        is_claim_review=True
    )
    idx, is_suff, notes = evidence_sufficiency_metric.compute_sufficiency([ev1, ev2])
    assert is_suff is True
    assert idx > 1.20
    assert any("ClaimReview" in n for n in notes)


def test_evidence_graph_and_audit_report():
    claim = AtomicClaim(
        id="c-graph-1",
        raw_text="The economy expanded by 7 percent",
        canonical_claim="The economy expanded by 7 percent",
        checkworthy_score=0.91,
        is_checkworthy=True
    )
    ev = EvidenceSnippet(
        id="e-g1",
        claim_id=claim.id,
        source_name="National Stats Bureau",
        source_url="https://stats.gov/report",
        domain="stats.gov",
        snippet_text="Official figures confirm 7 percent expansion.",
        retrieval_score=0.94,
        stance=StanceType.SUPPORTS,
        is_claim_review=True
    )
    audit = AuditTrail(
        summary="Official confirmation from statistics office.",
        supporting_citations=["https://stats.gov/report"],
        limitations=[]
    )
    report = audit_report_generator.generate_report(
        job_id="job-exp-01",
        claim=claim,
        evidence_items=[ev],
        verdict=VeracityLabel.SUPPORTED,
        raw_confidence=0.95,
        audit=audit
    )
    assert report.job_id == "job-exp-01"
    assert report.verdict == VeracityLabel.SUPPORTED
    assert len(report.evidence_graph.nodes) >= 3  # Claim, Evidence, Domain
    assert len(report.evidence_graph.edges) >= 2
    assert any(edge.relation == "SUPPORTS" for edge in report.evidence_graph.edges)
    assert any(edge.relation == "CITES" for edge in report.evidence_graph.edges)
