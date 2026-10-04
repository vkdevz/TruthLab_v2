"""Pipeline Profiling Script.
Measures actual wall-clock latencies across each individual stage of Phase 1:
- Claim extraction & decomposition
- Evidence retrieval
- Evidence ranking
- NLI stance inference
- Verdict engine evaluation
- End-to-end Text verification
- URL extraction & Anti-SSRF validation
"""

import asyncio
import time
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.evidence.provider import composite_evidence_retriever
from backend.app.evidence.ranking import hybrid_evidence_ranker
from backend.app.verification.nli import nli_interpreter
from backend.app.verification.verdict_engine import verdict_engine
from backend.app.services.pipeline_service import pipeline_service
from backend.app.ingestion.url_ingest import url_ingestion_service

SAMPLE_TEXT = "The central health ministry announced a complete ban on 5G network towers due to radiation concerns."
SAMPLE_URL = "https://example-news.org/articles/5g-update"


async def profile_pipeline():
    print("=" * 60)
    print("PROFILING PHASE 1 CORE VERIFICATION PIPELINE")
    print("=" * 60)

    timings = {}

    # 1. Claim Extraction Latency
    t0 = time.perf_counter()
    claims = claim_decomposer.decompose(SAMPLE_TEXT)
    t1 = time.perf_counter()
    timings["claim_extraction_ms"] = round((t1 - t0) * 1000, 2)
    print(f"1. Claim Extraction Latency: {timings['claim_extraction_ms']} ms ({len(claims)} claim(s) extracted)")

    claim = claims[0] if claims else None
    if not claim:
        print("Error: No claims extracted.")
        return

    # 2. Evidence Retrieval Latency
    t0 = time.perf_counter()
    raw_evidence = await composite_evidence_retriever.retrieve_candidate_evidence(
        claim_id=claim.id,
        canonical_claim=claim.canonical_claim,
        search_queries=claim.search_queries,
        per_query_limit=4
    )
    t1 = time.perf_counter()
    timings["evidence_retrieval_ms"] = round((t1 - t0) * 1000, 2)
    print(f"2. Evidence Retrieval Latency: {timings['evidence_retrieval_ms']} ms ({len(raw_evidence)} items retrieved)")

    # 3. Evidence Ranking Latency
    t0 = time.perf_counter()
    ranked = hybrid_evidence_ranker.rank_evidence(
        claim_text=claim.canonical_claim,
        candidate_evidence=raw_evidence,
        top_k=5
    )
    t1 = time.perf_counter()
    timings["evidence_ranking_ms"] = round((t1 - t0) * 1000, 2)
    print(f"3. Evidence Ranking Latency: {timings['evidence_ranking_ms']} ms ({len(ranked)} items ranked)")

    # 4. NLI Inference Latency
    t0 = time.perf_counter()
    stanced = nli_interpreter.process_evidence_stances(
        claim_text=claim.canonical_claim,
        evidence_items=ranked
    )
    t1 = time.perf_counter()
    timings["nli_interpretation_ms"] = round((t1 - t0) * 1000, 2)
    print(f"4. NLI Stance Interpretation Latency: {timings['nli_interpretation_ms']} ms")

    # 5. Verdict Engine Latency
    t0 = time.perf_counter()
    result = verdict_engine.evaluate_veracity(
        claim=claim,
        evidence_items=stanced
    )
    t1 = time.perf_counter()
    timings["verdict_engine_ms"] = round((t1 - t0) * 1000, 2)
    print(f"5. Verdict Engine Latency: {timings['verdict_engine_ms']} ms (Verdict: {result.veracity.value})")

    # 6. End-to-End Text Pipeline Latency
    t0 = time.perf_counter()
    full_resp = await pipeline_service.verify_text(SAMPLE_TEXT)
    t1 = time.perf_counter()
    timings["e2e_text_verification_ms"] = round((t1 - t0) * 1000, 2)
    print(f"6. End-to-End Text Verification Latency: {timings['e2e_text_verification_ms']} ms")

    # 7. URL Ingestion & Verification Latency (mocking network fetch safely)
    mock_article = {
        "title": "Telecom Authority Clarifies Spectrum Allocation",
        "publication_date": "2025-01-15",
        "text": "The Ministry confirmed that all telecom operators are continuing 5G rollouts without any bans.",
        "source_domain": "reuters.com",
        "canonical_url": SAMPLE_URL,
    }
    with patch.object(url_ingestion_service, "ingest_url", new=AsyncMock(return_value=mock_article)):
        t0 = time.perf_counter()
        url_resp = await pipeline_service.verify_url(SAMPLE_URL)
        t1 = time.perf_counter()
        timings["e2e_url_verification_ms"] = round((t1 - t0) * 1000, 2)
        print(f"7. End-to-End URL Verification Latency: {timings['e2e_url_verification_ms']} ms")

    # Save to docs/experiments/pipeline_latency.json
    out_dir = Path("docs/experiments")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "pipeline_latency.json"
    with open(out_file, "w") as f:
        json.dump(timings, f, indent=2)

    print(f"\nLatency profile successfully saved to: {out_file}")
    return timings


if __name__ == "__main__":
    asyncio.run(profile_pipeline())
