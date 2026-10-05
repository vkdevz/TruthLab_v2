"""Systematic Error Analysis and Failure Categorization Framework.

Categorizes system errors across:
- RETRIEVAL_FAILURE
- STANCE_INTERPRETATION_FAILURE
- TEMPORAL_FAILURE
- SOURCE_CREDIBILITY_FAILURE
- OCR_FAILURE
- ASR_FAILURE
- CROSS_MODAL_MISMATCH
- INSUFFICIENT_EVIDENCE
- AMBIGUOUS_CLAIM
- LABEL_AMBIGUITY
- DATASET_ARTIFACT
- UNSUPPORTED_CLAIM

Presents real empirical examples from benchmark executions without fabricated data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


ERROR_TAXONOMY_DESCRIPTIONS = {
    "RETRIEVAL_FAILURE": "Target evidence exists in reality, but retrieval query formulation or lexical mismatch missed the snippet.",
    "STANCE_INTERPRETATION_FAILURE": "Relevant evidence was retrieved, but NLI/stance classifier misclassified the stance.",
    "TEMPORAL_FAILURE": "Temporal verifier failed to resolve outdated recycling or misjudged event occurrence vs publication date.",
    "SOURCE_CREDIBILITY_FAILURE": "Low-reputation source corrupted the decision matrix.",
    "OCR_FAILURE": "Visual text overlay unreadable or corrupted by compression artifacts.",
    "ASR_FAILURE": "Speech transcription dropped or missed verbal claim propositions.",
    "CROSS_MODAL_MISMATCH": "Out-of-context caption pairing ('cheapfake') was not properly penalized.",
    "INSUFFICIENT_EVIDENCE": "No authoritative public evidence exists; system properly withheld factual verdict.",
    "AMBIGUOUS_CLAIM": "Subjective or non-falsifiable language hindered discrete verification.",
    "LABEL_AMBIGUITY": "Fine-grained boundary between MISLEADING and CONTRADICTED caused target disagreement.",
    "DATASET_ARTIFACT": "Annotation guideline nuance in external fact-checking benchmark.",
    "UNSUPPORTED_CLAIM": "Private or unverified assertion lacking any external corroboration.",
}


@dataclass
class FailureCase:
    sample_id: str
    claim_text: str
    modality: str
    gold_verdict: str
    predicted_verdict: str
    confidence: float
    uncertainty_level: str
    primary_failure_category: str
    root_cause_explanation: str
    remediation_strategy: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def categorize_error(
    sample: Dict[str, Any],
    pred_verdict: str,
    confidence: float,
    evidence_count: int,
    supporting_count: int,
    refuting_count: int,
    temporal_status: str,
) -> FailureCase:
    gold = sample["gold_verdict"]
    cid = sample["id"]
    txt = sample["text"]
    modality = sample.get("modality", "text")

    # Diagnose root cause based on observable pipeline signals
    if gold == "OUTDATED" and pred_verdict != "OUTDATED":
        cat = "TEMPORAL_FAILURE"
        cause = f"Temporal verifier assigned status '{temporal_status}' rather than recognizing historical event recycling."
        remed = "Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs."
    elif gold == "INSUFFICIENT_EVIDENCE" and pred_verdict != "INSUFFICIENT_EVIDENCE":
        cat = "RETRIEVAL_FAILURE" if evidence_count > 0 else "LABEL_AMBIGUITY"
        cause = f"Retrieved {evidence_count} tangential snippets that falsely inflated evidence sufficiency."
        remed = "Increase strictness of semantic relevance thresholding before admitting snippets to fusion."
    elif gold in ("CONTRADICTED", "MISLEADING") and pred_verdict == "SUPPORTED":
        cat = "STANCE_INTERPRETATION_FAILURE"
        cause = f"Stance classifier yielded {supporting_count} support hits on refuting context."
        remed = "Incorporate fine-tuned DeBERTa-v3 NLI model to replace rule-based lexical stance matcher."
    elif gold == "MISLEADING" and pred_verdict == "CONTRADICTED":
        cat = "LABEL_AMBIGUITY"
        cause = "Nuanced distinction between partially true/misleading claims and absolute contradiction."
        remed = "Calibrate decision matrix threshold separating severe distortion (CONTRADICTED) from partial truth (MISLEADING)."
    elif evidence_count == 0 and gold != "INSUFFICIENT_EVIDENCE":
        cat = "RETRIEVAL_FAILURE"
        cause = "Zero evidence passages retrieved for a testable empirical proposition."
        remed = "Integrate multi-query query expansion with BM25 + dense neural retrieval backends."
    elif modality in ("text+image", "text+video") and pred_verdict != gold:
        cat = "CROSS_MODAL_MISMATCH"
        cause = "Media forensic signals did not sufficiently weight visual anomaly in decision matrix."
        remed = "Refine cross-modal alignment penalty weights in multimodal fusion matrix."
    else:
        cat = "LABEL_AMBIGUITY"
        cause = f"Fine-grained disagreement between gold label '{gold}' and system verdict '{pred_verdict}'."
        remed = "Standardize cross-annotator benchmark guidelines across multi-class veracity boundaries."

    uncertainty_level = "LOW" if confidence >= 0.85 else ("MODERATE" if confidence >= 0.60 else "HIGH")

    return FailureCase(
        sample_id=cid,
        claim_text=txt,
        modality=modality,
        gold_verdict=gold,
        predicted_verdict=pred_verdict,
        confidence=round(confidence, 3),
        uncertainty_level=uncertainty_level,
        primary_failure_category=cat,
        root_cause_explanation=cause,
        remediation_strategy=remed,
    )


def error_analysis_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Inspects benchmark evaluation results and generates structured error taxonomy."""
    # Load test split and evidence-aware results
    res_path = Path("research/results/evidence_aware_benchmark.json")
    if not res_path.exists():
        from research.experiments.evidence_aware_benchmark import run_evidence_aware_benchmark
        run_evidence_aware_benchmark()

    with open(res_path, "r", encoding="utf-8") as f:
        ev_benchmark = json.load(f)

    with open("data/processed/test.json", "r", encoding="utf-8") as f:
        test_samples = json.load(f)

    sample_evals = ev_benchmark["results"]["sample_evaluations"]
    sample_map = {s["id"]: s for s in test_samples}

    identified_failures: List[FailureCase] = []

    for ev in sample_evals:
        sid = ev["id"]
        sample = sample_map.get(sid)
        if not sample:
            continue

        gold = sample["gold_verdict"]
        pred = ev["predicted_5class"]

        if gold != pred:
            failure = categorize_error(
                sample=sample,
                pred_verdict=pred,
                confidence=ev.get("confidence", 0.5),
                evidence_count=ev.get("evidence_count", 0),
                supporting_count=ev.get("supporting_count", 0),
                refuting_count=ev.get("refuting_count", 0),
                temporal_status=ev.get("temporal_status", "UNKNOWN"),
            )
            identified_failures.append(failure)

    # Calculate category breakdown
    category_counts: Dict[str, int] = {}
    for f in identified_failures:
        category_counts[f.primary_failure_category] = category_counts.get(f.primary_failure_category, 0) + 1

    total_errors = len(identified_failures)
    category_percentages = {
        k: round(v / max(1, total_errors) * 100, 1) for k, v in category_counts.items()
    }

    # Generate Markdown documentation
    md_path = Path("docs/experiments/ERROR_ANALYSIS.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Systematic Error Analysis & Failure Taxonomy\n\n")
        f.write(f"- **Total Evaluated Claims (Test Set)**: {len(sample_evals)}\n")
        f.write(f"- **Total Misclassifications**: {total_errors}\n")
        f.write(f"- **System Accuracy**: {round((len(sample_evals) - total_errors) / len(sample_evals) * 100, 1)}%\n\n")
        f.write("## 1. Failure Category Breakdown\n\n")
        f.write("| Failure Category | Count | Percentage | Description |\n")
        f.write("|------------------|-------|------------|-------------|\n")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            pct = category_percentages[cat]
            desc = ERROR_TAXONOMY_DESCRIPTIONS.get(cat, "")
            f.write(f"| `{cat}` | {count} | {pct}% | {desc} |\n")

        f.write("\n## 2. Empirical Failure Cases & Root Cause Analysis\n\n")
        for i, case in enumerate(identified_failures, 1):
            f.write(f"### Case {i}: [{case.sample_id}] {case.primary_failure_category}\n")
            f.write(f"- **Claim**: \"{case.claim_text}\"\n")
            f.write(f"- **Modality**: `{case.modality}`\n")
            f.write(f"- **Gold Verdict**: `{case.gold_verdict}` | **Predicted**: `{case.predicted_verdict}`\n")
            f.write(f"- **Confidence**: {case.confidence} (Uncertainty: `{case.uncertainty_level}`)\n")
            f.write(f"- **Root Cause**: {case.root_cause_explanation}\n")
            f.write(f"- **Remediation**: {case.remediation_strategy}\n\n")

    return {
        "benchmark_type": "RESEARCH_BENCHMARK",
        "description": "Systematic failure categorization on benchmark evaluation runs",
        "total_test_samples": len(sample_evals),
        "total_misclassifications": total_errors,
        "category_counts": category_counts,
        "category_percentages": category_percentages,
        "failure_cases": [f.to_dict() for f in identified_failures],
    }


def run_error_analysis() -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_id="EXP-14-ERROR-ANALYSIS",
        name="systematic_error_analysis",
        description="Empirical failure analysis and taxonomy classification",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(error_analysis_experiment)

    out_path = Path("research/results/error_analysis.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    return res


if __name__ == "__main__":
    run_error_analysis()
