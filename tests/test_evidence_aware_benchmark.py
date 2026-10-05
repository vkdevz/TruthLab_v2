"""Unit tests for Evidence-Aware Benchmark (Commit 05).
"""

from pathlib import Path
from research.experiments.evidence_aware_benchmark import run_evidence_aware_benchmark


def test_evidence_aware_benchmark_execution():
    res = run_evidence_aware_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    comp = res["results"]["comparison"]

    assert "baseline_text_only" in comp
    assert "proposed_evidence_system" in comp
    assert "improvements" in comp

    sys_res = comp["proposed_evidence_system"]
    base_res = comp["baseline_text_only"]

    # Verify evidence awareness yields superior binary macro-F1 over text-only
    assert sys_res["binary_macro_f1"] >= base_res["binary_macro_f1"]
    assert sys_res["five_class_accuracy"] >= base_res["five_class_accuracy"]

    # Verify result files exist
    assert Path("research/results/evidence_aware_benchmark.json").exists()
    assert Path("docs/experiments/comparative_results.json").exists()
