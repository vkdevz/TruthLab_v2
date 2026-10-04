import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.claim.checkworthiness import checkworthiness_scorer
from backend.app.ml.claim.entity_extractor import entity_extractor
from backend.app.ml.claim.query_generator import query_generator
from backend.app.ml.claim.decomposer import claim_decomposer


def test_checkworthiness_scorer():
    # Empirical claim with number and factual verb
    score_factual, is_factual = checkworthiness_scorer.score(
        "The central bank increased the benchmark interest rate by 50 basis points."
    )
    assert is_factual is True
    assert score_factual >= 0.60

    # Subjective opinion
    score_opinion, is_opinion = checkworthiness_scorer.score(
        "In my opinion this movie was completely boring and terrible."
    )
    assert is_opinion is False
    assert score_opinion < 0.50

    # Rhetorical question
    score_question, is_question = checkworthiness_scorer.score(
        "Why is everyone talking about this new trend?"
    )
    assert is_question is False
    assert score_question < 0.30


def test_entity_and_temporal_extractor():
    text = "On March 15, the World Health Organization reported new guidelines in Geneva."
    entities, temporal_anchor, inferred_date = entity_extractor.extract(text)
    
    assert "World Health Organization" in entities or "Geneva" in entities
    assert temporal_anchor is not None
    assert "March 15" in temporal_anchor or "15" in temporal_anchor


def test_query_generator():
    claim = "India launched Chandrayaan-3 to the lunar south pole in 2023"
    entities = ["India", "Chandrayaan-3"]
    queries = query_generator.generate_queries(claim, entities, temporal_anchor="2023")
    
    assert len(queries) >= 2
    assert any("fact check" in q for q in queries)


def test_claim_decomposer_compound_text():
    corpus = (
        "The minister announced a major tax reform, and officials confirmed it takes effect in 2025. "
        "In my opinion, this policy is wonderful!"
    )
    claims = claim_decomposer.decompose(corpus)
    
    assert len(claims) >= 2
    # First statement should be check-worthy
    assert any(c.is_checkworthy for c in claims)
    # The opinion statement should have lower checkworthy score
    opinion_claim = [c for c in claims if "wonderful" in c.raw_text.lower()]
    if opinion_claim:
        assert opinion_claim[0].checkworthy_score < 0.60


@pytest.mark.asyncio
async def test_claims_api_extract():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/claims/extract", json={
            "text": "The aerospace organization launched a communication satellite on Tuesday, and engineers verified solar array deployment."
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total_claims"] >= 2
        assert data["checkworthy_count"] >= 1
        assert len(data["claims"][0]["search_queries"]) > 0
