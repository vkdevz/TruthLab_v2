"""Unit tests for Robustness Benchmark (Commit 13).
"""

from pathlib import Path
from research.experiments.robustness_benchmark import (
    perturb_capitalization,
    perturb_noisy_ocr,
    perturb_punctuation,
    perturb_spelling,
    run_robustness_benchmark,
)


def test_perturbation_functions():
    text = "The NASA scientists reported atmospheric findings."
    p_spell = perturb_spelling(text, seed=42)
    p_punct = perturb_punctuation("Hello, world! How are you?")
    p_caps = perturb_capitalization("evidence")
    p_ocr = perturb_noisy_ocr("common words")

    assert "," not in p_punct
    assert "!" not in p_punct
    assert p_caps != "evidence"
    assert "rn" in p_ocr  # 'm' replaced by 'rn'


def test_robustness_benchmark_execution():
    res = run_robustness_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    evals = res["results"]["perturbation_evaluations"]

    assert "clean_baseline" in evals
    assert "spelling_noise" in evals
    assert "reordered_evidence_shuffled" in evals
    assert res["results"]["robustness_summary"]["permutation_invariance_maintained"] is True
    assert Path("research/results/robustness_benchmark.json").exists()
