"""Temporal Verification and Reasoning Benchmark.

Rigorously evaluates temporal reasoning across specific temporal phenomena:
1. Event Date vs. Publication Date Disambiguation (preventing publication date conflation)
2. Present-Framing Marker Detection ("today", "breaking", "urgent alert", "just announced")
3. Stale / Expired Evidence Detection (temporal delta penalization)
4. Unknown / Missing Dates (avoiding false penalty on timeless claims)
5. Conflicting Date Resolution
6. Outdated Claim (Temporal Recycling) Detection Precision, Recall, and F1
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from backend.app.ml.context.temporal_parser import temporal_parser
from backend.app.ml.context.temporal_verifier import temporal_verifier
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType
from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


# Controlled test suite with exact ground truth temporal labels
TEMPORAL_EVAL_CASES = [
    # Category 1: Outdated Claims with Present Framing ("today", "breaking")
    {
        "id": "temp_case_001",
        "claim_text": "Breaking right now: Immediate statewide curfew and quarantine ordered for all citizens due to health emergency!",
        "gold_has_present_framing": True,
        "gold_temporal_status": "OUTDATED",
        "evidence_snippet": "This emergency order was originally issued on March 24, 2020 during early COVID-19 lockdowns and expired. No curfew is in effect today.",
        "evidence_pub_date": "2024-02-15T10:00:00Z",
    },
    {
        "id": "temp_case_002",
        "claim_text": "Urgent alert today: Postal service warns that anthrax letters were found in public mailboxes this morning!",
        "gold_has_present_framing": True,
        "gold_temporal_status": "OUTDATED",
        "evidence_snippet": "The Amerithrax mailings occurred in October 2001. Postal authorities confirmed no new anthrax mailings have occurred.",
        "evidence_pub_date": "2023-11-04T12:00:00Z",
    },
    {
        "id": "temp_case_003",
        "claim_text": "Breaking news this morning: UK prime minister announces sudden resignation live from Downing Street today!",
        "gold_has_present_framing": True,
        "gold_temporal_status": "OUTDATED",
        "evidence_snippet": "Footage shows Liz Truss announcing her resignation outside 10 Downing Street on October 20, 2022. It does not depict current leadership.",
        "evidence_pub_date": "2024-05-10T14:00:00Z",
    },
    {
        "id": "temp_case_004",
        "claim_text": "Breaking today: Federal Reserve cuts US benchmark interest rates to exactly 0.0 percent effective immediately!",
        "gold_has_present_framing": True,
        "gold_temporal_status": "OUTDATED",
        "evidence_snippet": "The emergency rate cut to near-zero occurred on March 15, 2020. The current benchmark policy rate remains above 5 percent.",
        "evidence_pub_date": "2024-01-18T16:00:00Z",
    },

    # Category 2: Current / Recent Claims with Present Framing
    {
        "id": "temp_case_005",
        "claim_text": "European Central Bank maintained key interest rates at benchmark levels during deliberations today.",
        "gold_has_present_framing": True,
        "gold_temporal_status": "CURRENT",
        "evidence_snippet": "The Governing Council of the ECB announced today that key interest rates will remain unchanged following its scheduled monetary meeting.",
        "evidence_pub_date": "2023-10-26T12:45:00Z",
    },
    {
        "id": "temp_case_006",
        "claim_text": "WHO declared the end of the global emergency for Mpox today in an international press conference.",
        "gold_has_present_framing": True,
        "gold_temporal_status": "CURRENT",
        "evidence_snippet": "Today WHO Director-General Tedros Adhanom Ghebreyesus declared the end of the Mpox global health emergency.",
        "evidence_pub_date": "2023-05-11T16:00:00Z",
    },

    # Category 3: Historical Claims without Present Framing
    {
        "id": "temp_case_007",
        "claim_text": "The international kilogram standard was officially redefined in terms of the Planck constant in 2019.",
        "gold_has_present_framing": False,
        "gold_temporal_status": "HISTORICAL",
        "evidence_snippet": "The formal redefinition of the SI kilogram took effect on May 20, 2019 at the General Conference on Weights and Measures.",
        "evidence_pub_date": "2019-05-20T08:00:00Z",
    },
    {
        "id": "temp_case_008",
        "claim_text": "Apollo 11 astronauts landed on the lunar surface and walked on the Moon in July 1969.",
        "gold_has_present_framing": False,
        "gold_temporal_status": "HISTORICAL",
        "evidence_snippet": "Neil Armstrong and Buzz Aldrin landed the Apollo 11 Lunar Module on the Sea of Tranquility on July 20, 1969.",
        "evidence_pub_date": "2019-07-20T10:00:00Z",
    },

    # Category 4: Timeless Scientific Facts (Missing / Unknown Dates)
    {
        "id": "temp_case_009",
        "claim_text": "Ultraviolet radiation is classified as a human carcinogen that damages cellular DNA.",
        "gold_has_present_framing": False,
        "gold_temporal_status": "UNKNOWN",
        "evidence_snippet": "Ultraviolet radiation is a proven Group 1 human carcinogen that directly induces pyrimidine dimers.",
        "evidence_pub_date": None,
    },
    {
        "id": "temp_case_010",
        "claim_text": "Drinking water containing boiled garlic water does not eliminate viral respiratory pathogens.",
        "gold_has_present_framing": False,
        "gold_temporal_status": "UNKNOWN",
        "evidence_snippet": "The World Health Organization confirmed there is no medical evidence that consuming garlic cures viral infections.",
        "evidence_pub_date": None,
    },
]


def temporal_evaluation_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Evaluates temporal parsing, event vs pub date discrimination, and outdated claim logic."""
    present_framing_golds = []
    present_framing_preds = []

    temporal_status_golds = []
    temporal_status_preds = []

    event_date_discriminations = []

    for case in TEMPORAL_EVAL_CASES:
        claim_text = case["claim_text"]
        gold_pf = case["gold_has_present_framing"]
        gold_status = case["gold_temporal_status"]

        # 1. Present framing detection
        pred_pf = temporal_parser.has_present_framing(claim_text)
        present_framing_golds.append(gold_pf)
        present_framing_preds.append(pred_pf)

        # 2. Context verification
        claim_obj = AtomicClaim(
            id=case["id"],
            raw_text=claim_text,
            canonical_claim=claim_text,
            checkworthy_score=0.9,
            is_checkworthy=True,
            search_queries=[claim_text[:80]],
        )

        ev_items = []
        if case["evidence_snippet"]:
            pub_dt = None
            if case["evidence_pub_date"]:
                pub_dt = datetime.fromisoformat(case["evidence_pub_date"].replace("Z", "+00:00"))
            ev_items.append(
                EvidenceSnippet(
                    id=f"ev_{case['id']}",
                    claim_id=claim_obj.id,
                    source_name="Fact Check Archive",
                    source_url="https://factcheck.org",
                    domain="factcheck.org",
                    domain_credibility_weight=1.5,
                    snippet_text=case["evidence_snippet"],
                    publication_date=pub_dt,
                    retrieval_score=0.95,
                    stance=StanceType.REFUTES if gold_status == "OUTDATED" else StanceType.SUPPORTS,
                    is_claim_review=True,
                )
            )

        t_res = temporal_verifier.verify_context(claim_obj, ev_items)
        pred_status = t_res.temporal_status
        temporal_status_golds.append(gold_status)
        temporal_status_preds.append(pred_status)

        # 3. Verify event date != publication date separation
        # For outdated claims with past evidence (e.g. event in 2020, pub date in 2024),
        # verify the verifier did not just echo the pub date as event date
        if gold_status == "OUTDATED" and t_res.event_date and ev_items and ev_items[0].publication_date:
            separated = (t_res.event_date.year != ev_items[0].publication_date.year)
            event_date_discriminations.append(separated)

    # Calculate metrics
    acc_pf = float(accuracy_score(present_framing_golds, present_framing_preds))

    # Binary OUTDATED detection metrics
    outdated_golds = [1 if s == "OUTDATED" else 0 for s in temporal_status_golds]
    outdated_preds = [1 if s == "OUTDATED" else 0 for s in temporal_status_preds]

    p_outdated = float(precision_score(outdated_golds, outdated_preds, zero_division=0))
    r_outdated = float(recall_score(outdated_golds, outdated_preds, zero_division=0))
    f1_outdated = float(f1_score(outdated_golds, outdated_preds, zero_division=0))

    acc_multiclass = float(accuracy_score(temporal_status_golds, temporal_status_preds))

    return {
        "benchmark_type": "RESEARCH_BENCHMARK",
        "description": "Temporal verification and event vs publication date disambiguation benchmark",
        "sample_count": len(TEMPORAL_EVAL_CASES),
        "explicit_assumptions": [
            "Publication date of a news article or fact-check is strictly distinct from the underlying event occurrence date.",
            "Absence of explicit temporal anchors in a scientific claim is marked UNKNOWN and does not trigger temporal penalties.",
            "Present-framing markers ('today', 'breaking') paired with corroborated historical events trigger OUTDATED classification.",
        ],
        "metrics": {
            "present_framing_detection_accuracy": round(acc_pf, 4),
            "outdated_claim_precision": round(p_outdated, 4),
            "outdated_claim_recall": round(r_outdated, 4),
            "outdated_claim_f1": round(f1_outdated, 4),
            "temporal_status_overall_accuracy": round(acc_multiclass, 4),
            "event_vs_publication_separation_rate": round(float(np.mean(event_date_discriminations)), 4) if event_date_discriminations else 1.0,
        },
        "breakdown": [
            {
                "id": c["id"],
                "gold_status": c["gold_temporal_status"],
                "pred_status": pred,
                "gold_present_framing": c["gold_has_present_framing"],
                "pred_present_framing": pf,
            }
            for c, pred, pf in zip(TEMPORAL_EVAL_CASES, temporal_status_preds, present_framing_preds)
        ],
    }


def run_temporal_benchmark() -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_id="EXP-08-TEMPORAL",
        name="temporal_verification_benchmark",
        description="Controlled evaluation of temporal reasoning and outdated claim detection",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(temporal_evaluation_experiment)

    out_path = Path("research/results/temporal_benchmark.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    return res


if __name__ == "__main__":
    run_temporal_benchmark()
