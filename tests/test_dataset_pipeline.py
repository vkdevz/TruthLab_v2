"""Unit tests for Dataset Acquisition and Pipeline (Commit 02).
"""

from pathlib import Path
from research.data.pipeline import (
    DatasetPipeline,
    DatasetSample,
    CURATED_VERIFICATION_RECORDS,
    LABEL_MAPPING,
)


def test_label_mapping_coverage():
    assert LABEL_MAPPING["true"] == "SUPPORTED"
    assert LABEL_MAPPING["false"] == "CONTRADICTED"
    assert LABEL_MAPPING["mostly false"] == "MISLEADING"
    assert LABEL_MAPPING["outdated"] == "OUTDATED"
    assert LABEL_MAPPING["unproven"] == "INSUFFICIENT_EVIDENCE"


def test_dataset_pipeline_stratification(tmp_path):
    pipeline = DatasetPipeline(seed=42)
    samples = pipeline.harmonize_records()
    assert len(samples) == len(CURATED_VERIFICATION_RECORDS)

    train, val, test = pipeline.stratified_split(samples)
    assert len(train) + len(val) + len(test) == len(samples)

    manifest = pipeline.build_and_export(output_dir=tmp_path)
    assert manifest.total_samples == len(samples)
    assert (tmp_path / "train.json").exists()
    assert (tmp_path / "val.json").exists()
    assert (tmp_path / "test.json").exists()
    assert (tmp_path / "manifest.json").exists()
