import asyncio
import json
from pathlib import Path
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.services.retrieval.web_retriever import web_retriever
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.fusion.fusion_model import multimodal_fusion_model
from backend.app.schemas.media import ImageForensicIndicators

ABLATION_CASES = [
    {
        "desc": "Recycled 2020 Curfew",
        "text": "Breaking right now: Curfew announced across the entire state due to health emergency!",
        "expected_full": "OUTDATED",
        "expected_no_temporal": "CONTRADICTED",  # Without temporal module, falls back to raw refutation/contradiction
    },
    {
        "desc": "Cheapfake Caption Mismatch",
        "text": "Violent riots break out downtown",
        "ocr": "Annual Summer Carnival and Parade 2019",
        "expected_full": "MISLEADING",
        "expected_no_alignment": "INSUFFICIENT_EVIDENCE",  # Without alignment, misses cheapfake signature
    },
    {
        "desc": "Verified Exoplanet Discovery",
        "text": "James Webb Space Telescope detected atmospheric carbon dioxide on WASP-39b",
        "expected_full": "SUPPORTED",
        "expected_no_reranker": "SUPPORTED",
    }
]


async def run_ablation_study():
    print("=" * 65)
    print("Executing Phase 11: Ablation Study")
    print("=" * 65)

    ablation_records = []

    for case in ABLATION_CASES:
        claims = claim_decomposer.decompose(case["text"])
        c = claims[0]
        raw_ev = await web_retriever.retrieve_evidence(c.id, c.canonical_claim, c.search_queries)
        reranked_ev = evidence_reranker.rerank(c.canonical_claim, raw_ev)
        stanced_ev = stance_classifier.evaluate_evidence_stances(c.canonical_claim, reranked_ev)

        # 1. Full Pipeline
        full_decision = multimodal_fusion_model.fuse(
            claim=c,
            evidence_items=stanced_ev,
            ocr_text=case.get("ocr")
        )

        # 2. Ablation: Without Cross-Modal Alignment
        no_align_decision = multimodal_fusion_model.fuse(
            claim=c,
            evidence_items=stanced_ev,
            ocr_text=None  # Stripped visual OCR
        )

        rec = {
            "case": case["desc"],
            "full_system_verdict": full_decision.final_verdict.value,
            "ablation_no_alignment_verdict": no_align_decision.final_verdict.value,
            "full_confidence": full_decision.confidence,
            "ablation_confidence": no_align_decision.confidence,
        }
        ablation_records.append(rec)
        print(f"\nCase: {case['desc']}")
        print(f"  Full Pipeline Verdict: {rec['full_system_verdict']} (Conf: {rec['full_confidence']})")
        print(f"  No Alignment Verdict : {rec['ablation_no_alignment_verdict']} (Conf: {rec['ablation_confidence']})")

    out_file = Path("docs/experiments/ablation_results.json")
    with open(out_file, "w") as f:
        json.dump(ablation_records, f, indent=2)

    print(f"\nAblation study logged to: {out_file}")
    return ablation_records


if __name__ == "__main__":
    asyncio.run(run_ablation_study())
