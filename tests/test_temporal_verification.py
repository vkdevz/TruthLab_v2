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

    # Unknown location case
    unknown_status, _ = geolocation_matcher.check_consistency(
        "Scientific discovery announced in lab",
        ["Researchers observed quantum superposition in superconductor."]
    )
    assert unknown_status == "UNKNOWN"


def test_historical_claim_not_outdated():
    """A claim about a legitimate past event (e.g. 1969 Moon Landing) should be HISTORICAL, not OUTDATED."""
    claim = AtomicClaim(
        id="c-hist",
        raw_text="In 1969, Apollo 11 successfully landed astronauts on the Moon.",
        canonical_claim="Apollo 11 successfully landed astronauts on the Moon in 1969",
        checkworthy_score=0.90,
        is_checkworthy=True,
    )
    ev = EvidenceSnippet(
        id="e-hist",
        claim_id=claim.id,
        source_name="NASA History",
        source_url="https://history.nasa.gov/apollo11",
        domain="nasa.gov",
        snippet_text="Apollo 11 landed on the lunar surface on July 20, 1969.",
        publication_date=datetime(2019, 7, 20, tzinfo=timezone.utc),
        retrieval_score=0.95,
        stance=StanceType.SUPPORTS,
        stance_probabilities={"SUPPORTS": 0.98, "REFUTES": 0.01, "NEUTRAL": 0.01},
    )

    res = temporal_verifier.verify_context(claim, [ev])
    assert res.temporal_status == "HISTORICAL"
    assert res.is_outdated is False
    assert res.is_anachronistic is False


def test_event_date_vs_publication_date_distinction():
    """Recent article (published yesterday) reporting on a historical event from 2018."""
    claim = AtomicClaim(
        id="c-dist",
        raw_text="Breaking today: Severe power grid failure leaves city in dark!",
        canonical_claim="Severe power grid failure leaves city in dark",
        checkworthy_score=0.92,
        is_checkworthy=True,
    )
    ev = EvidenceSnippet(
        id="e-dist",
        claim_id=claim.id,
        source_name="FactCheck Archive",
        source_url="https://factcheck.org/recycled-blackout",
        domain="factcheck.org",
        snippet_text="Viral video originally occurred on March 14, 2018 during a localized substation transformer blast.",
        publication_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        retrieval_score=0.92,
        stance=StanceType.SUPPORTS,
        stance_probabilities={"SUPPORTS": 0.90, "REFUTES": 0.05, "NEUTRAL": 0.05},
        is_claim_review=True,
    )

    res = temporal_verifier.verify_context(claim, [ev])
    assert res.temporal_status == "OUTDATED"
    assert res.is_outdated is True
    # The event date should reflect 2018 rather than being conflated with 2024
    assert res.event_date is not None
    assert res.event_date.year == 2018
    assert res.source_date is not None


def test_unknown_date_preserves_uncertainty():
    """Claim and evidence with no detectable timestamps preserve uncertainty as UNKNOWN."""
    claim = AtomicClaim(
        id="c-unk",
        raw_text="Mysterious glowing rocks discovered by local geologist.",
        canonical_claim="Glowing rocks discovered by local geologist",
        checkworthy_score=0.65,
        is_checkworthy=True,
    )
    ev = EvidenceSnippet(
        id="e-unk",
        claim_id=claim.id,
        source_name="Geology Blog",
        source_url="https://example.com/rocks",
        domain="example.com",
        snippet_text="Fluorescent minerals glow brightly when exposed to ultraviolet light rays.",
        publication_date=None,
        retrieval_score=0.70,
        stance=StanceType.NEUTRAL,
        stance_probabilities={"SUPPORTS": 0.2, "REFUTES": 0.2, "NEUTRAL": 0.6},
    )

    res = temporal_verifier.verify_context(claim, [ev])
    assert res.temporal_status == "UNKNOWN"
    assert res.is_outdated is False
    assert res.delta_days is None


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
    assert result.temporal_status == "OUTDATED"
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

