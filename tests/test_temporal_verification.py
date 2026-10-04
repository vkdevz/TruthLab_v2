from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.context.temporal_parser import temporal_parser
from backend.app.ml.context.geolocation_matcher import geolocation_matcher
from backend.app.ml.context.temporal_verifier import temporal_verifier
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType, VeracityLabel


def test_temporal_parser_urgency_markers():
    assert temporal_parser.has_present_framing("Breaking: major emergency declared today!") is True
    assert temporal_parser.has_present_framing("In 2018, parliament passed the transport bill.") is False

    anchor, dt = temporal_parser.parse_text_timestamp("The event happened in 2021.")
    assert anchor == "2021"
    assert dt.year == 2021


def test_geolocation_matcher():
    status, notes = geolocation_matcher.check_consistency(
        "Severe flood hits Florida overnight",
        ["Devastating typhoon caused widespread flooding in the Philippines."]
    )
    assert status == "MISMATCH"
    assert len(notes) > 0


def test_outdated_claim_classification():
    # A genuine 2020 lockdown order being shared as "breaking right now"
    claim = AtomicClaim(
        id="c-temp-1",
        raw_text="Breaking: Curfew announced across the entire state due to health emergency!",
        canonical_claim="Curfew announced across the entire state due to health emergency",
        checkworthy_score=0.92,
        is_checkworthy=True,
    )

    ev = EvidenceSnippet(
        id="e-temp-1",
        claim_id=claim.id,
        source_name="PolitiFact",
        source_url="https://www.politifact.com/factchecks/2020/mar/state-curfew-lockdown/",
        domain="politifact.com",
        snippet_text="This emergency order was issued during the March 2020 lockdowns and expired years ago.",
        publication_date=datetime(2020, 3, 24, tzinfo=timezone.utc),
        retrieval_score=0.90,
        stance=StanceType.SUPPORTS,  # Event actually happened in 2020!
        stance_probabilities={"SUPPORTS": 0.90, "REFUTES": 0.05, "NEUTRAL": 0.05},
        is_claim_review=True,
    )

    result = temporal_verifier.verify_context(claim, [ev])
    assert result.is_outdated is True
    assert result.delta_days is not None
    assert result.delta_days > 365
    assert len(result.temporal_notes) > 0


@pytest.mark.asyncio
async def test_api_outdated_claim_verdict():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/verify/claim", json={
            "text": "Breaking right now: Curfew announced across the entire state due to health emergency!"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total_claims_processed"] >= 1
        result = data["results"][0]
        # Should be classified as OUTDATED rather than SUPPORTED or CONTRADICTED
        assert result["veracity"] == "OUTDATED"
        assert result["is_temporal_mismatch"] is True
        assert len(result["audit"]["temporal_notes"]) > 0
