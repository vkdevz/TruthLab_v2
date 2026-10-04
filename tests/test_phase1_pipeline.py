import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException

from backend.app.main import app
from backend.app.ingestion.url_ingest import URLValidator, url_ingestion_service
from backend.app.ingestion.text_ingest import text_ingestion_service
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.ml.claim.checkworthiness import checkworthiness_scorer
from backend.app.evidence.provider import LocalClaimReviewProvider, composite_evidence_retriever
from backend.app.evidence.ranking import hybrid_evidence_ranker
from backend.app.verification.nli import nli_interpreter
from backend.app.verification.verdict_engine import verdict_engine
from backend.app.schemas.veracity import VeracityLabel, StanceType
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet


# =====================================================================
# 1. URL VALIDATION & SSRF TESTS
# =====================================================================

def test_ssrf_protection_blocked_hosts():
    """Verify localhost and loopback hosts are rejected immediately."""
    blocked_urls = [
        "http://localhost:8000/admin",
        "http://127.0.0.1:5000/secret",
        "http://0.0.0.0/debug",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]
    for url in blocked_urls:
        with pytest.raises(HTTPException) as exc_info:
            URLValidator.validate_url(url)
        assert exc_info.value.status_code == 400


def test_ssrf_protection_schemes():
    """Verify non-HTTP(S) schemes are blocked."""
    invalid_schemes = [
        "ftp://example.com/file.txt",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "gopher://example.com",
    ]
    for url in invalid_schemes:
        with pytest.raises(HTTPException) as exc_info:
            URLValidator.validate_url(url)
        assert exc_info.value.status_code == 400
        assert "Unsupported URL scheme" in exc_info.value.detail


def test_ssrf_private_ip_blocking():
    """Verify private subnet resolution is blocked."""
    with patch("socket.getaddrinfo") as mock_dns:
        # Mock DNS resolving to private IP 192.168.1.50
        mock_dns.return_value = [(2, 1, 6, "", ("192.168.1.50", 80))]
        with pytest.raises(HTTPException) as exc_info:
            URLValidator.validate_url("https://internal-service.local/news")
        assert exc_info.value.status_code == 400
        assert "prohibited" in exc_info.value.detail.lower()


# =====================================================================
# 2. TEXT INGESTION & NORMALIZATION TESTS
# =====================================================================

def test_text_normalization():
    """Verify whitespace cleaning and Unicode NFKC normalization."""
    raw_input = "  India   has   banned \xa0 5G\t\tservices.  \n\n\n\nNew regulation passed.  "
    cleaned = text_ingestion_service.ingest_text(raw_input)
    assert "India has banned 5G services." in cleaned
    assert "\t" not in cleaned
    assert "\n\n\n" not in cleaned


def test_text_length_boundaries():
    """Verify minimum and maximum length bounds."""
    with pytest.raises(HTTPException) as exc_info:
        text_ingestion_service.ingest_text("Hi")
    assert exc_info.value.status_code == 400
    assert "too short" in exc_info.value.detail.lower()

    with pytest.raises(HTTPException) as exc_info:
        text_ingestion_service.ingest_text("A" * 30000)
    assert exc_info.value.status_code == 413


# =====================================================================
# 3. CLAIM INTELLIGENCE & DECOMPOSITION TESTS
# =====================================================================

def test_claim_decomposition():
    """Verify compound sentence decomposition into atomic propositions."""
    compound_text = "The government banned 5G network towers, and scientists reported new safety guidelines."
    claims = claim_decomposer.decompose(compound_text)
    assert len(claims) >= 2
    assert any("5g" in c.canonical_claim.lower() for c in claims)
    assert any("guidelines" in c.canonical_claim.lower() or "safety" in c.canonical_claim.lower() for c in claims)


def test_checkworthiness_scorer():
    """Verify factual claims are distinguished from subjective opinions."""
    factual = "WHO announced 15000 new clinical trials in 2024."
    score_f, is_cw_f = checkworthiness_scorer.score(factual)
    assert is_cw_f is True
    assert score_f >= 0.60

    opinion = "In my opinion, this movie is an awesome masterpiece."
    score_o, is_cw_o = checkworthiness_scorer.score(opinion)
    assert is_cw_o is False
    assert score_o < 0.60


# =====================================================================
# 4. EVIDENCE ENGINE & RANKING TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_evidence_retrieval_and_ranking():
    """Verify retrieval from local ClaimReview index and hybrid ranking."""
    provider = LocalClaimReviewProvider()
    results = await provider.retrieve("5G towers coronavirus health ministry ban", claim_id="c-test")
    assert len(results) > 0
    assert results[0].is_claim_review is True

    # Test hybrid ranker
    ranked = hybrid_evidence_ranker.rank_evidence(
        claim_text="Government bans 5G towers due to health radiation",
        candidate_evidence=results,
        top_k=3
    )
    assert len(ranked) <= 3
    assert ranked[0].retrieval_score > 0.0


# =====================================================================
# 5. NLI RELATIONSHIP TESTS
# =====================================================================

def test_nli_interpreter_relationships():
    """Verify NLI detects SUPPORTS, REFUTES, and NEUTRAL relationships."""
    claim = "Government announced nationwide ban on 5G network towers."

    # Refuting evidence
    refuting_snippet = "Official fact check: The government denied claims of banning 5G. The claim is completely false."
    stance, probs = nli_interpreter.evaluate_relationship(claim, refuting_snippet)
    assert stance == StanceType.REFUTES
    assert probs["REFUTES"] > probs["SUPPORTS"]

    # Supporting evidence
    supporting_snippet = "Ministry confirmed and verified the official published announcement today."
    stance_s, probs_s = nli_interpreter.evaluate_relationship(claim, supporting_snippet)
    assert stance_s == StanceType.SUPPORTS
    assert probs_s["SUPPORTS"] > probs_s["REFUTES"]


# =====================================================================
# 6. FIVE-CLASS VERDICT & SUFFICIENCY TESTS
# =====================================================================

def test_verdict_engine_insufficient_evidence():
    """Verify that insufficient evidence triggers INSUFFICIENT_EVIDENCE."""
    claim = AtomicClaim(
        id="c-1",
        raw_text="Aliens landed in Central Park yesterday.",
        canonical_claim="Aliens landed in Central Park yesterday.",
        checkworthy_score=0.8,
        is_checkworthy=True,
        entities=["Central Park"],
        temporal_anchor=None,
        inferred_date=None,
        search_queries=["Aliens landed in Central Park"]
    )
    # Empty evidence
    result = verdict_engine.evaluate_veracity(claim, evidence_items=[])
    assert result.veracity == VeracityLabel.INSUFFICIENT_EVIDENCE
    assert result.evidence_sufficiency_score == 0.0
    assert "inadequate" in result.audit.summary.lower()


def test_verdict_engine_contradicted():
    """Verify that decisive refuting evidence triggers CONTRADICTED."""
    claim = AtomicClaim(
        id="c-2",
        raw_text="India banned all 5G services in 2025.",
        canonical_claim="India banned all 5G services in 2025.",
        checkworthy_score=0.85,
        is_checkworthy=True,
        entities=["India", "5G"],
        temporal_anchor="2025",
        inferred_date=None,
        search_queries=["India banned 5G"]
    )
    refuting_item = EvidenceSnippet(
        id="ev-1",
        claim_id="c-2",
        source_name="PIB Fact Check",
        source_url="https://factcheck.pib.gov.in/5g-ban",
        domain="factcheck.pib.gov.in",
        domain_credibility_weight=1.8,
        snippet_text="PIB debunked this viral notice: The government has NOT banned 5G services. The circular is false and fake.",
        retrieval_score=0.92,
        stance=StanceType.REFUTES,
        stance_probabilities={"SUPPORTS": 0.02, "REFUTES": 0.95, "NEUTRAL": 0.03},
        is_claim_review=True,
        claim_review_rating="False"
    )
    result = verdict_engine.evaluate_veracity(claim, [refuting_item])
    assert result.veracity == VeracityLabel.CONTRADICTED
    assert result.confidence <= 0.96  # Calibrated upper limit


# =====================================================================
# 7. INTEGRATION TESTS (API: TEXT & URL & GET /verification/{id})
# =====================================================================

@pytest.mark.asyncio
async def test_integration_text_verification_endpoint():
    """End-to-end integration test: POST /api/v1/verify/text and GET /api/v1/verification/{id}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit claim to verify
        payload = {"text": "India has banned all 5G services due to health hazards."}
        response = await client.post("/api/v1/verify/text", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["input_modality"] == "TEXT"
        assert data["overall_veracity"] in [v.value for v in VeracityLabel]
        assert data["overall_confidence"] > 0.0
        assert len(data["claims_verified"]) >= 1
        assert "evidence_graph" in data
        assert "executive_summary" in data
        assert len(data["system_limitations"]) >= 1

        # Retrieve verification record by ID
        job_id = data["job_id"]
        get_resp = await client.get(f"/api/v1/verification/{job_id}")
        assert get_resp.status_code == 200
        job_data = get_resp.json()
        assert job_data["status"] == "COMPLETED"
        assert job_data["progress_percent"] == 100
        assert job_data["result"]["job_id"] == job_id


@pytest.mark.asyncio
async def test_integration_url_verification_endpoint():
    """End-to-end integration test: POST /api/v1/verify/url with mocked article fetch."""
    mock_article = {
        "title": "Telecom Authority Clarifies Spectrum Allocation",
        "publication_date": "2025-01-15",
        "text": "The Ministry confirmed that all telecom operators are continuing 5G rollouts across the nation without any bans or interruptions.",
        "source_domain": "reuters.com",
        "canonical_url": "https://www.reuters.com/business/telecom-5g-update",
    }

    with patch.object(url_ingestion_service, "ingest_url", new=AsyncMock(return_value=mock_article)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {"url": "https://www.reuters.com/business/telecom-5g-update"}
            response = await client.post("/api/v1/verify/url", json=payload)
            assert response.status_code == 200
            data = response.json()

            assert data["input_modality"] == "URL"
            assert "job_id" in data
            assert len(data["claims_verified"]) >= 1
            assert data["evidence_graph"] is not None
            assert data["executive_summary"] != ""
