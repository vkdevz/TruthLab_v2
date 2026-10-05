"""Unit tests for Ablation Framework (Commit 07).
"""

from pathlib import Path
from research.experiments.ablation_study import run_ablation_study


def test_ablation_study_execution():
    res = run_ablation_study()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    configs = res["results"]["ablation_configurations"]

    assert "A_text_only" in configs
    assert "B_text_evidence" in configs
    assert "C_text_evidence_temporal" in configs
    assert "D_text_evidence_media" in configs
    assert "E_full_multimodal" in configs

    for cfg_key, cfg in configs.items():
        assert 0.0 <= cfg["five_class_accuracy"] <= 1.0
        assert 0.0 <= cfg["five_class_macro_f1"] <= 1.0
        assert "per_class_f1" in cfg
        assert "confusion_matrix" in cfg

    assert "marginal_contributions" in res["results"]
    assert Path("research/results/ablation_benchmark.json").exists()
    assert Path("docs/experiments/ablation_results.json").exists()
