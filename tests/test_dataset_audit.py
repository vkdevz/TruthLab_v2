"""Unit tests for Dataset Quality Audit (Commit 03).
"""

from research.data.audit import DatasetAuditor, run_audit


def test_auditor_clean_dataset():
    report = run_audit()
    assert report.audit_passed is True
    assert len(report.exact_duplicates) == 0
    assert len(report.train_test_leakages) == 0
    assert len(report.missing_value_errors) == 0
    assert len(report.malformed_records) == 0
    assert report.total_records == 60


def test_auditor_detects_leakage():
    sample1 = {"id": "1", "text": "Claim A", "canonical_claim": "Claim A", "modality": "text", "gold_verdict": "SUPPORTED", "gold_binary": 0}
    sample2 = {"id": "2", "text": "Claim A", "canonical_claim": "Claim A", "modality": "text", "gold_verdict": "SUPPORTED", "gold_binary": 0}

    auditor = DatasetAuditor(train_samples=[sample1], val_samples=[], test_samples=[sample2])
    report = auditor.audit()
    assert report.audit_passed is False
    assert len(report.train_test_leakages) == 1
