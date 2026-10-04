import json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from backend.app.ml.baseline.classifier import baseline_classifier
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.services.retrieval.web_retriever import web_retriever
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.nli.veracity_scorer import veracity_scorer
from backend.app.ml.fusion.fusion_model import multimodal_fusion_model
from backend.app.ml.explainability.calibration import confidence_calibrator
from backend.app.schemas.veracity import VeracityLabel
from backend.app.schemas.media import ImageForensicIndicators
import asyncio

BENCHMARK_EVAL_SUITE = [
    # 1. Contradicted claims
    {"text": "Bananas and boiled garlic water cure coronavirus infections completely", "gold_verdict": "CONTRADICTED", "gold_binary": 1},
    {"text": "NASA scientists officially confirmed alien signals received today", "gold_verdict": "CONTRADICTED", "gold_binary": 1},
    {"text": "Government secretly puts microscopic tracking chips inside drinking water supplies", "gold_verdict": "CONTRADICTED", "gold_binary": 1},
    
    # 2. Supported claims
    {"text": "James Webb Space Telescope detected atmospheric carbon dioxide on WASP-39b", "gold_verdict": "SUPPORTED", "gold_binary": 0},
    {"text": "India launched Chandrayaan-3 and landed successfully near the lunar south pole", "gold_verdict": "SUPPORTED", "gold_binary": 0},
    {"text": "Researchers published peer-reviewed findings on solar cell efficiency in Nature", "gold_verdict": "SUPPORTED", "gold_binary": 0},
    
    # 3. Outdated claims (temporal recycling)
    {"text": "Breaking right now: Curfew announced across the entire state due to health emergency!", "gold_verdict": "OUTDATED", "gold_binary": 1},
    
    # 4. Insufficient evidence claims
    {"text": "My local neighbor's cousin invented an invisible anti-gravity bicycle yesterday", "gold_verdict": "INSUFFICIENT_EVIDENCE", "gold_binary": 1},
]


async def run_comparative_benchmarks():
    print("=" * 65)
    print("Executing Phase 11: Controlled Comparative Experiments")
    print("=" * 65)

    y_gold_5class = [item["gold_verdict"] for item in BENCHMARK_EVAL_SUITE]
    y_gold_binary = [item["gold_binary"] for item in BENCHMARK_EVAL_SUITE]

    # Model 1: Baseline Text-Only Classifier (Phase 3)
    baseline_preds_binary = []
    for item in BENCHMARK_EVAL_SUITE:
        p = baseline_classifier.predict(item["text"])
        baseline_preds_binary.append(1 if p.label == "FAKE" else 0)

    acc_base = accuracy_score(y_gold_binary, baseline_preds_binary)
    f1_base = f1_score(y_gold_binary, baseline_preds_binary, average="macro")

    print(f"\n[EXP-01 Baseline Text-Only]:")
    print(f"  Binary Accuracy: {acc_base:.4f} | Macro-F1: {f1_base:.4f}")

    # Model 2: Proposed Multimodal Evidence-Aware Verification System
    system_preds_5class = []
    system_preds_binary = []

    for item in BENCHMARK_EVAL_SUITE:
        claims = claim_decomposer.decompose(item["text"])
        c = claims[0]
        raw_ev = await web_retriever.retrieve_evidence(c.id, c.canonical_claim, c.search_queries)
        reranked_ev = evidence_reranker.rerank(c.canonical_claim, raw_ev)
        stanced_ev = stance_classifier.evaluate_evidence_stances(c.canonical_claim, reranked_ev)
        
        # Multimodal fusion
        decision = multimodal_fusion_model.fuse(claim=c, evidence_items=stanced_ev)
        v_label = decision.final_verdict.value
        system_preds_5class.append(v_label)
        
        # Binary projection: SUPPORTED = 0 (Real), all others = 1 (Misinformation/Unverified)
        system_preds_binary.append(0 if v_label == "SUPPORTED" else 1)

    acc_sys_bin = accuracy_score(y_gold_binary, system_preds_binary)
    f1_sys_bin = f1_score(y_gold_binary, system_preds_binary, average="macro")
    acc_sys_5class = accuracy_score(y_gold_5class, system_preds_5class)
    f1_sys_5class = f1_score(y_gold_5class, system_preds_5class, average="macro")

    print(f"\n[EXP-05 Proposed Multimodal Evidence System]:")
    print(f"  Binary Accuracy: {acc_sys_bin:.4f} | Macro-F1: {f1_sys_bin:.4f}")
    print(f"  5-Class Veracity Accuracy: {acc_sys_5class:.4f} | 5-Class Macro-F1: {f1_sys_5class:.4f}")

    results = {
        "sample_count": len(BENCHMARK_EVAL_SUITE),
        "baseline_text_only": {
            "binary_accuracy": round(float(acc_base), 4),
            "macro_f1": round(float(f1_base), 4),
        },
        "proposed_evidence_system": {
            "binary_accuracy": round(float(acc_sys_bin), 4),
            "binary_macro_f1": round(float(f1_sys_bin), 4),
            "five_class_accuracy": round(float(acc_sys_5class), 4),
            "five_class_macro_f1": round(float(f1_sys_5class), 4),
        },
        "f1_improvement": round(float(f1_sys_bin - f1_base), 4),
    }

    out_file = Path("docs/experiments/comparative_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults successfully logged to: {out_file}")
    return results


if __name__ == "__main__":
    asyncio.run(run_comparative_benchmarks())
