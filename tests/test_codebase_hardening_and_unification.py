import io
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from backend.app.main import app
from backend.app.services.scraper import scraper_service
from backend.app.services.job_manager import job_manager
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.evidence.ranking import hybrid_evidence_ranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.verification.nli import nli_interpreter
from backend.app.ml.nli.veracity_scorer import veracity_scorer
from backend.app.verification.verdict_engine import verdict_engine
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType, VeracityLabel


@pytest.mark.asyncio
async def test_scraper_service_hardened_ssrf_blocking():
    """Verify scraper_service enforces strict Anti-SSRF via URLValidator."""
    blocked = [
        "http://localhost:9000/secret",
        "http://127.0.0.1:8000/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
        "http://172.16.0.1/private",
        "ftp://example.com/file",
        "gopher://example.com/",
    ]
    for url in blocked:
        with pytest.raises(HTTPException) as exc_info:
            scraper_service.validate_url_safety(url)
        assert exc_info.value.status_code == 400


def test_stance_classifier_unification():
    """Verify StanceClassifier delegates to NLIEvidenceInterpreter and results are identical."""
    claim = "Scientists discover water on Mars"
    evidence = "NASA published confirmation of liquid water channels on Mars."
    
    s_stance, s_probs = stance_classifier.predict_stance(claim, evidence)
    n_stance, n_probs = nli_interpreter.evaluate_relationship(claim, evidence)
    
    assert s_stance == n_stance == StanceType.SUPPORTS
    assert s_probs == n_probs


def test_reranker_unification():
    """Verify EvidenceReranker delegates to HybridEvidenceRanker."""
    claim = "COVID-19 vaccine mRNA technology"
    ev1 = EvidenceSnippet(
        id="ev1",
        claim_id="c1",
        source_name="Health Source",
        source_url="https://health.gov/covid",
        domain="health.gov",
        domain_credibility_weight=1.6,
        snippet_text="mRNA vaccines use modified RNA to teach cells how to respond.",
        retrieval_score=0.8,
        stance=StanceType.SUPPORTS,
        stance_probabilities={"SUPPORTS": 0.9, "REFUTES": 0.05, "NEUTRAL": 0.05},
        is_claim_review=False
    )
    reranked = evidence_reranker.rerank(claim, [ev1])
    ranked = hybrid_evidence_ranker.rank_evidence(claim, [ev1])
    assert len(reranked) == len(ranked) == 1
    assert reranked[0].id == ranked[0].id


def test_veracity_scorer_unification():
    """Verify VeracityScorer delegates to FiveClassVerdictEngine."""
    claim = AtomicClaim(
        id="c1",
        raw_text="The moon is made of green cheese",
        canonical_claim="The moon is made of green cheese",
        checkworthy_score=0.9,
        is_checkworthy=True,
    )
    res_scorer = veracity_scorer.score_claim(claim, [])
    res_engine = verdict_engine.evaluate_veracity(claim, [])
    assert res_scorer.veracity == res_engine.veracity == VeracityLabel.INSUFFICIENT_EVIDENCE
    assert res_scorer.confidence == res_engine.confidence


@pytest.mark.asyncio
async def test_ingest_executes_real_verification_in_background():
    """Verify /api/v1/ingest/text executes the actual verification pipeline and updates job payload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/ingest/text", json={
            "text": "NASA James Webb Space Telescope confirmed detection of carbon dioxide on exoplanet WASP-39b."
        })
        assert res.status_code == 200
        data = res.json()
        job_id = data["job_id"]
        
        # Poll status
        poll_res = await ac.get(f"/api/v1/jobs/{job_id}")
        assert poll_res.status_code == 200
        job_status = poll_res.json()
        assert job_status["job_id"] == job_id
        # As FastAPI BackgroundTasks run synchronously in TestClient/ASGITransport, it completes immediately
        assert job_status["status"] == "COMPLETED"
        assert job_status["result"] is not None
        assert "overall_veracity" in job_status["result"]
        assert job_status["result"]["overall_veracity"] in [v.value for v in VeracityLabel]


@pytest.mark.asyncio
async def test_ingest_media_no_internal_path_leak_and_completes_job():
    """Verify /api/v1/ingest/media does not leak internal server paths (Principle 14) and completes verification."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {"file": ("neutral_sample.png", io.BytesIO(dummy_png), "image/png")}
        
        res = await ac.post("/api/v1/ingest/media", files=files, data={"is_video": False})
        assert res.status_code == 200
        data = res.json()
        assert "job_id" in data
        assert "saved_path" not in data, "Internal filesystem path must never be exposed to API consumers."
        assert "file_id" in data
        
        poll_res = await ac.get(f"/api/v1/jobs/{data['job_id']}")
        assert poll_res.status_code == 200
        job_status = poll_res.json()
        assert job_status["status"] == "COMPLETED"
        assert job_status["result"]["overall_veracity"] == "INSUFFICIENT_EVIDENCE"


def test_decision_matrix_distributions_sum_to_one():
    """Verify all 6 decision matrix branches produce probability distributions summing to exactly 1.0."""
    from backend.app.ml.fusion.decision_matrix import decision_matrix
    from backend.app.schemas.fusion import FusionFeatureVector

    # 1. Refutation dominance
    f1 = FusionFeatureVector(stance_refute_score=0.85, stance_support_score=0.05, evidence_sufficiency=2.0)
    d1 = decision_matrix.resolve(f1)
    assert abs(sum(d1.verdict_distribution.values()) - 1.0) < 1e-5
    assert d1.verdict_distribution["CONTRADICTED"] == d1.confidence

    # 2. Cross-modal mismatch / media manipulation
    f2 = FusionFeatureVector(stance_refute_score=0.1, stance_support_score=0.5, cross_modal_alignment=0.4, evidence_sufficiency=2.0)
    d2 = decision_matrix.resolve(f2)
    assert abs(sum(d2.verdict_distribution.values()) - 1.0) < 1e-5
    assert d2.verdict_distribution["MISLEADING"] == d2.confidence

    # 3. Temporal recycling
    f3 = FusionFeatureVector(stance_refute_score=0.1, stance_support_score=0.5, temporal_penalty=0.8, evidence_sufficiency=2.0)
    d3 = decision_matrix.resolve(f3)
    assert abs(sum(d3.verdict_distribution.values()) - 1.0) < 1e-5
    assert d3.verdict_distribution["OUTDATED"] == d3.confidence

    # 4. Evidence insufficiency
    f4 = FusionFeatureVector(stance_refute_score=0.1, stance_support_score=0.1, evidence_sufficiency=0.3)
    d4 = decision_matrix.resolve(f4)
    assert abs(sum(d4.verdict_distribution.values()) - 1.0) < 1e-5
    assert d4.verdict_distribution["INSUFFICIENT_EVIDENCE"] == d4.confidence

    # 5. Corroborated support
    f5 = FusionFeatureVector(stance_refute_score=0.05, stance_support_score=0.85, evidence_sufficiency=2.0)
    d5 = decision_matrix.resolve(f5)
    assert abs(sum(d5.verdict_distribution.values()) - 1.0) < 1e-5
    assert d5.verdict_distribution["SUPPORTED"] == d5.confidence

    # 6. Ambiguous / conflicting
    f6 = FusionFeatureVector(stance_refute_score=0.45, stance_support_score=0.45, evidence_sufficiency=2.0)
    d6 = decision_matrix.resolve(f6)
    assert abs(sum(d6.verdict_distribution.values()) - 1.0) < 1e-5
    assert d6.verdict_distribution["MISLEADING"] == d6.confidence


@pytest.mark.asyncio
async def test_evidence_providers_neutral_on_keyword_absence(monkeypatch):
    """Verify Wikipedia and DDG search snippets without explicit contradiction/entailment cues default to NEUTRAL."""
    from backend.app.evidence.provider import WikipediaEvidenceProvider, PublicWebSearchProvider
    import httpx

    # Mock Wikipedia response returning neutral snippet
    class MockWikiResponse:
        status_code = 200
        def json(self):
            return {
                "query": {
                    "search": [{
                        "title": "Jupiter Atmosphere",
                        "snippet": "Jupiter is the fifth planet from the Sun and the largest in the Solar System.",
                    }]
                }
            }

    async def mock_get(self, url, *args, **kwargs):
        return MockWikiResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    wiki = WikipediaEvidenceProvider()
    snippets = await wiki.retrieve("Jupiter atmosphere layers", claim_id="c_jup", limit=2)
    assert len(snippets) > 0
    assert snippets[0].stance == StanceType.NEUTRAL
    assert snippets[0].stance_probabilities["NEUTRAL"] == 0.80
