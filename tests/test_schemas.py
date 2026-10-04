from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from backend.app.schemas.veracity import VeracityLabel, StanceType, ModalityType
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.media import ImageForensicIndicators
from backend.app.schemas.verification import (
    FullVerificationResponse,
    ClaimVerificationResult,
    AuditTrail,
    EvidenceGraph,
    GraphNode,
    GraphEdge,
)


def test_atomic_claim_validation():
    claim = AtomicClaim(
        id="c-001",
        raw_text="The Indian economy grew by 8.2% in 2024 according to official reports.",
        canonical_claim="India's GDP grew by 8.2% in 2024.",
        checkworthy_score=0.92,
        is_checkworthy=True,
        entities=["India", "GDP", "2024"],
        temporal_anchor="2024",
        search_queries=["India GDP growth 2024 official data"]
    )
    assert claim.is_checkworthy is True
    assert claim.checkworthy_score == 0.92
    assert "India" in claim.entities

    # Out of range test
    with pytest.raises(ValidationError):
        AtomicClaim(
            id="c-002",
            raw_text="Test",
            canonical_claim="Test",
            checkworthy_score=1.5,  # Invalid: > 1.0
            is_checkworthy=True
        )


def test_evidence_snippet_validation():
    snippet = EvidenceSnippet(
        id="e-001",
        claim_id="c-001",
        source_name="Ministry of Statistics and Programme Implementation",
        source_url="https://mospi.gov.in/press-release-gdp-2024",
        domain="mospi.gov.in",
        domain_credibility_weight=1.5,
        snippet_text="Real GDP has grown by 8.2% in the financial year 2023-24.",
        retrieval_score=0.88,
        stance=StanceType.SUPPORTS,
        stance_probabilities={"SUPPORTS": 0.91, "REFUTES": 0.02, "NEUTRAL": 0.07},
        is_claim_review=False
    )
    assert snippet.stance == StanceType.SUPPORTS
    assert snippet.domain == "mospi.gov.in"


def test_full_verification_response_serialization():
    claim = AtomicClaim(
        id="c-001",
        raw_text="Breaking: NASA confirms alien signal received today.",
        canonical_claim="NASA confirmed receipt of an extraterrestrial radio signal today.",
        checkworthy_score=0.95,
        is_checkworthy=True
    )
    
    snippet = EvidenceSnippet(
        id="e-001",
        claim_id="c-001",
        source_name="NASA News",
        source_url="https://www.nasa.gov/news/press-release",
        domain="nasa.gov",
        snippet_text="NASA scientists clarify that anomalous signals were terrestrial radio frequency interference.",
        retrieval_score=0.94,
        stance=StanceType.REFUTES,
        stance_probabilities={"SUPPORTS": 0.01, "REFUTES": 0.96, "NEUTRAL": 0.03}
    )

    audit = AuditTrail(
        summary="NASA official communications refute the claim of extraterrestrial origin.",
        refuting_citations=["https://www.nasa.gov/news/press-release"],
        limitations=["Live social media chatter was not indexed."]
    )

    claim_res = ClaimVerificationResult(
        claim=claim,
        veracity=VeracityLabel.CONTRADICTED,
        confidence=0.94,
        evidence_sufficiency_score=1.85,
        evidence_items=[snippet],
        audit=audit
    )

    graph = EvidenceGraph(
        nodes=[
            GraphNode(id="c-001", label="Extraterrestrial Signal", type="claim", status="CONTRADICTED"),
            GraphNode(id="e-001", label="NASA Advisory", type="evidence", status="REFUTES"),
            GraphNode(id="s-nasa", label="nasa.gov", type="source")
        ],
        edges=[
            GraphEdge(source="e-001", target="c-001", relation="REFUTES", weight=0.96),
            GraphEdge(source="e-001", target="s-nasa", relation="CITES", weight=1.0)
        ]
    )

    now = datetime.now(timezone.utc)
    response = FullVerificationResponse(
        job_id="job-101",
        created_at=now,
        completed_at=now,
        input_modality=ModalityType.TEXT,
        overall_veracity=VeracityLabel.CONTRADICTED,
        overall_confidence=0.94,
        claims_verified=[claim_res],
        evidence_graph=graph,
        executive_summary="The claim that NASA confirmed an alien signal is explicitly contradicted by official NASA statements.",
        system_limitations=["Analysis based on indexed records up to query time."]
    )

    json_data = response.model_dump_json()
    assert "CONTRADICTED" in json_data
    assert "job-101" in json_data
