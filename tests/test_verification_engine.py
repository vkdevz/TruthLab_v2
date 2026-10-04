import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.retrieval.factcheck_cache import factcheck_cache_service
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.nli.veracity_scorer import veracity_scorer
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.schemas.veracity import VeracityLabel, StanceType


def test_factcheck_cache_retrieval():
    # Query for known fake claim
    results = factcheck_cache_service.search_local_cache("garlic cures coronavirus")
    assert len(results) >= 1
    assert results[0].stance == StanceType.REFUTES
    assert "reuters" in results[0].domain.lower() or "who" in results[0].source_name.lower()


def test_evidence_reranker():
    claim = "James Webb Space Telescope detected atmospheric carbon dioxide on WASP-39b"
    evidence_items = factcheck_cache_service.search_local_cache("carbon dioxide Webb WASP", threshold=0.1)
    assert len(evidence_items) > 0
    reranked = evidence_reranker.rerank(claim, evidence_items)
    assert reranked[0].retrieval_score >= 0.3


def test_stance_classifier_rules():
    stance_refute, probs_refute = stance_classifier.predict_stance(
        "Alien base found on Mars",
        "Scientists confirmed this story is a completely false hoax with no evidence."
    )
    assert stance_refute == StanceType.REFUTES
    assert probs_refute["REFUTES"] > 0.80

    stance_supp, probs_supp = stance_classifier.predict_stance(
        "Moon landing in 1969",
        "Historical archives and telemetry confirmed the successful landing in 1969."
    )
    assert stance_supp == StanceType.SUPPORTS
    assert probs_supp["SUPPORTS"] > 0.80


@pytest.mark.asyncio
async def test_full_claim_verification_contradicted():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/verify/claim", json={
            "text": "Breaking news: NASA scientists officially confirmed alien signals received today!"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total_claims_processed"] >= 1
        result = data["results"][0]
        assert result["veracity"] == "CONTRADICTED"
        assert result["confidence"] >= 0.70
        assert len(result["audit"]["refuting_citations"]) > 0


@pytest.mark.asyncio
async def test_full_claim_verification_insufficient():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/verify/claim", json={
            "text": "My local neighbor's cousin invented an invisible flying bicycle last night."
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total_claims_processed"] >= 1
        result = data["results"][0]
        # Obscure claim with zero evidence should resolve to INSUFFICIENT_EVIDENCE
        assert result["veracity"] == "INSUFFICIENT_EVIDENCE"
        assert result["evidence_sufficiency_score"] < 1.20
