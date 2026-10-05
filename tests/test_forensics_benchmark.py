"""Unit tests for Media Forensics Benchmark (Commit 10).
"""

from pathlib import Path
from research.experiments.forensics_benchmark import run_forensics_benchmark


def test_forensics_benchmark_execution():
    res = run_forensics_benchmark()
    assert res["results"]["benchmark_type"] == "RESEARCH_BENCHMARK"
    assert "scientific_integrity_status" in res["results"]
    assert "error_level_analysis" in res["results"]["results"]
    assert "metadata_forensics" in res["results"]["results"]
    assert "synthetic_heuristic" in res["results"]["results"]

    meta = res["results"]["results"]["metadata_forensics"]
    assert meta["tagged_software_detected"] == "Adobe Photoshop 2024"
    assert meta["tagged_has_exif"] is True
    assert meta["stripped_has_exif"] is False

    synth = res["results"]["results"]["synthetic_heuristic"]
    assert synth["validation_status"] == "EXPLICITLY_UNVALIDATED"
    assert Path("research/results/forensics_benchmark.json").exists()
