"""Dataset Quality Audit Suite.

Executes rigorous integrity audits across dataset splits:
- Exact and near-duplicate detection
- Train/Validation/Test data leakage
- Missing, empty, or malformed fields
- Inconsistent labels across identical or similar claims
- Class imbalance and modality distributions
- Multimodal signal consistency and media reference validation
"""

from __future__ import annotations

import difflib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np


VALID_VERDICTS = {"SUPPORTED", "CONTRADICTED", "MISLEADING", "OUTDATED", "INSUFFICIENT_EVIDENCE"}
VALID_MODALITIES = {"text", "text+image", "text+video"}


@dataclass
class AuditReport:
    total_records: int
    train_records: int
    val_records: int
    test_records: int
    exact_duplicates: List[Dict[str, Any]]
    near_duplicates: List[Dict[str, Any]]
    train_test_leakages: List[Dict[str, Any]]
    missing_value_errors: List[Dict[str, Any]]
    malformed_records: List[Dict[str, Any]]
    inconsistent_labels: List[Dict[str, Any]]
    class_distribution: Dict[str, int]
    class_imbalance_entropy: float
    modality_distribution: Dict[str, int]
    multimodal_mismatches: List[Dict[str, Any]]
    url_duplicates: Dict[str, List[str]]
    warnings: List[str]
    audit_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetAuditor:
    """Audits dataset splits for cleanliness, leakage, and schema compliance."""

    def __init__(
        self,
        train_samples: List[Dict[str, Any]],
        val_samples: List[Dict[str, Any]],
        test_samples: List[Dict[str, Any]],
        near_duplicate_threshold: float = 0.85,
    ):
        self.train_samples = train_samples
        self.val_samples = val_samples
        self.test_samples = test_samples
        self.all_samples = train_samples + val_samples + test_samples
        self.near_duplicate_threshold = near_duplicate_threshold

    def audit(self) -> AuditReport:
        warnings: List[str] = []
        missing_errors: List[Dict[str, Any]] = []
        malformed: List[Dict[str, Any]] = []
        multimodal_mismatches: List[Dict[str, Any]] = []

        # 1. Inspect required fields, malformed types, and multimodal signals
        for s in self.all_samples:
            sid = s.get("id", "UNKNOWN")
            for req_field in ["id", "text", "canonical_claim", "modality", "gold_verdict", "gold_binary"]:
                if req_field not in s or s[req_field] is None or s[req_field] == "":
                    missing_errors.append({"id": sid, "field": req_field, "error": "missing_or_empty"})

            # Verdict validity
            v = s.get("gold_verdict")
            if v not in VALID_VERDICTS:
                malformed.append({"id": sid, "field": "gold_verdict", "invalid_value": v})

            # Binary validity
            b = s.get("gold_binary")
            if b not in (0, 1):
                malformed.append({"id": sid, "field": "gold_binary", "invalid_value": b})

            # Modality validity
            m = s.get("modality")
            if m not in VALID_MODALITIES:
                malformed.append({"id": sid, "field": "modality", "invalid_value": m})

            # Multimodal signal completeness
            if m == "text+image":
                signals = s.get("media_signals", {})
                if not isinstance(signals, dict) or not any(k in signals for k in ["has_splicing", "ela_high_risk", "synthetic_heuristic_score"]):
                    multimodal_mismatches.append({"id": sid, "modality": m, "reason": "missing_image_forensic_signals"})
            elif m == "text+video":
                signals = s.get("media_signals", {})
                if not isinstance(signals, dict) or not any(k in signals for k in ["has_asr_transcript", "overlay_ocr_matches"]):
                    multimodal_mismatches.append({"id": sid, "modality": m, "reason": "missing_video_signals"})

        # 2. Exact Duplicates & URL Duplicates
        seen_ids: Dict[str, str] = {}
        seen_texts: Dict[str, str] = {}
        exact_duplicates: List[Dict[str, Any]] = []
        url_map: Dict[str, List[str]] = {}

        for s in self.all_samples:
            sid = s.get("id")
            txt = s.get("text", "").strip().lower()
            url = s.get("source_url", "").strip()

            if sid in seen_ids:
                exact_duplicates.append({"type": "duplicate_id", "id": sid})
            seen_ids[sid] = sid

            if txt in seen_texts:
                exact_duplicates.append({"type": "duplicate_text", "id1": seen_texts[txt], "id2": sid, "text": txt})
            seen_texts[txt] = sid

            if url:
                url_map.setdefault(url, []).append(sid)

        url_duplicates = {u: ids for u, ids in url_map.items() if len(ids) > 1}

        # 3. Near Duplicates & Inconsistent Labels
        near_duplicates: List[Dict[str, Any]] = []
        inconsistent_labels: List[Dict[str, Any]] = []
        n = len(self.all_samples)
        for i in range(n):
            for j in range(i + 1, n):
                s1 = self.all_samples[i]
                s2 = self.all_samples[j]
                t1 = s1.get("text", "").lower()
                t2 = s2.get("text", "").lower()
                sim = difflib.SequenceMatcher(None, t1, t2).ratio()
                if sim >= self.near_duplicate_threshold:
                    near_duplicates.append({
                        "id1": s1["id"],
                        "id2": s2["id"],
                        "similarity": round(sim, 3),
                        "text1": s1["text"],
                        "text2": s2["text"],
                    })
                    if s1.get("gold_verdict") != s2.get("gold_verdict"):
                        inconsistent_labels.append({
                            "id1": s1["id"],
                            "id2": s2["id"],
                            "verdict1": s1.get("gold_verdict"),
                            "verdict2": s2.get("gold_verdict"),
                        })

        # 4. Train / Val / Test Leakage
        train_texts = {s.get("text", "").strip().lower(): s["id"] for s in self.train_samples}
        val_texts = {s.get("text", "").strip().lower(): s["id"] for s in self.val_samples}
        test_texts = {s.get("text", "").strip().lower(): s["id"] for s in self.test_samples}

        train_test_leakages: List[Dict[str, Any]] = []
        for t_text, t_id in test_texts.items():
            if t_text in train_texts:
                train_test_leakages.append({
                    "split_pair": "train_test",
                    "train_id": train_texts[t_text],
                    "test_id": t_id,
                    "text": t_text,
                })
        for v_text, v_id in val_texts.items():
            if v_text in train_texts:
                train_test_leakages.append({
                    "split_pair": "train_val",
                    "train_id": train_texts[v_text],
                    "val_id": v_id,
                    "text": v_text,
                })

        # 5. Class Balance and Entropy
        class_dist: Dict[str, int] = {}
        for s in self.all_samples:
            v = s.get("gold_verdict", "UNKNOWN")
            class_dist[v] = class_dist.get(v, 0) + 1

        probs = [count / n for count in class_dist.values()]
        entropy = float(-np.sum([p * np.log2(p) for p in probs if p > 0]))

        # Modality distribution
        modality_dist: Dict[str, int] = {}
        for s in self.all_samples:
            m = s.get("modality", "unknown")
            modality_dist[m] = modality_dist.get(m, 0) + 1

        if len(url_duplicates) > 0:
            warnings.append(f"Found {len(url_duplicates)} URLs shared across multiple claim records (fact-check landing pages).")

        audit_passed = (
            len(missing_errors) == 0
            and len(malformed) == 0
            and len(exact_duplicates) == 0
            and len(train_test_leakages) == 0
            and len(inconsistent_labels) == 0
            and len(multimodal_mismatches) == 0
        )

        return AuditReport(
            total_records=n,
            train_records=len(self.train_samples),
            val_records=len(self.val_samples),
            test_records=len(self.test_samples),
            exact_duplicates=exact_duplicates,
            near_duplicates=near_duplicates,
            train_test_leakages=train_test_leakages,
            missing_value_errors=missing_errors,
            malformed_records=malformed,
            inconsistent_labels=inconsistent_labels,
            class_distribution=class_dist,
            class_imbalance_entropy=round(entropy, 4),
            modality_distribution=modality_dist,
            multimodal_mismatches=multimodal_mismatches,
            url_duplicates=url_duplicates,
            warnings=warnings,
            audit_passed=audit_passed,
        )


def run_audit(data_dir: str | Path = "data/processed") -> AuditReport:
    dpath = Path(data_dir)
    with open(dpath / "train.json", "r", encoding="utf-8") as f:
        train = json.load(f)
    with open(dpath / "val.json", "r", encoding="utf-8") as f:
        val = json.load(f)
    with open(dpath / "test.json", "r", encoding="utf-8") as f:
        test = json.load(f)

    auditor = DatasetAuditor(train, val, test)
    report = auditor.audit()

    out_file = Path("research/results/dataset_quality_audit.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    # Generate Markdown summary
    md_file = Path("docs/experiments/DATASET_AUDIT.md")
    md_file.parent.mkdir(parents=True, exist_ok=True)
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# Dataset Quality Audit Report\n\n")
        f.write(f"- **Audit Status**: {'PASSED (Zero Critical Issues)' if report.audit_passed else 'FAILED'}\n")
        f.write(f"- **Total Records Audited**: {report.total_records}\n")
        f.write(f"- **Train / Val / Test**: {report.train_records} / {report.val_records} / {report.test_records}\n")
        f.write(f"- **Exact Duplicates**: {len(report.exact_duplicates)}\n")
        f.write(f"- **Near Duplicates**: {len(report.near_duplicates)}\n")
        f.write(f"- **Train-Test Data Leakage**: {len(report.train_test_leakages)}\n")
        f.write(f"- **Missing Value Errors**: {len(report.missing_value_errors)}\n")
        f.write(f"- **Malformed Records**: {len(report.malformed_records)}\n")
        f.write(f"- **Inconsistent Labels**: {len(report.inconsistent_labels)}\n")
        f.write(f"- **Multimodal Mismatches**: {len(report.multimodal_mismatches)}\n")
        f.write(f"- **Class Entropy**: {report.class_imbalance_entropy} (Maximum for 5 classes: 2.3219)\n\n")
        f.write("### Class Distribution\n")
        for k, v in report.class_distribution.items():
            pct = round(v / report.total_records * 100, 1)
            f.write(f"- `{k}`: {v} ({pct}%)\n")
        f.write("\n### Modality Distribution\n")
        for k, v in report.modality_distribution.items():
            pct = round(v / report.total_records * 100, 1)
            f.write(f"- `{k}`: {v} ({pct}%)\n")
        if report.warnings:
            f.write("\n### Audit Warnings\n")
            for w in report.warnings:
                f.write(f"- {w}\n")

    print(f"[+] Audit completed: Passed={report.audit_passed}. Report saved to {out_file} and {md_file}")
    return report


if __name__ == "__main__":
    run_audit()
