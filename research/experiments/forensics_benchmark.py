"""Media Forensic Signals Benchmark.

Evaluates auxiliary media forensic detectors under controlled conditions:
1. Error Level Analysis (ELA) on pristine vs. spliced/recompressed images
2. Metadata & EXIF Forensics (software tag detection, C2PA manifest scanning)
3. Synthetic Media Heuristic (Laplacian high-frequency variance & chromatic saturation)

Scientific Integrity Disclaimers:
- EXIF metadata is easily stripped or edited by web platforms. EXIF presence != proof of authenticity.
- ELA variance indicates compression anomalies; it does NOT constitute definitive proof of malicious tampering.
- Synthetic-media heuristic is an exploratory statistical signal; it is explicitly UNVALIDATED as a general AI detector.
"""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from PIL import Image, ImageDraw

from backend.app.ml.image.ela_forensics import ELAForensics
from backend.app.ml.image.metadata_forensics import MetadataForensics
from backend.app.ml.image.synthetic_detector import HeuristicFrequencySyntheticDetector
from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


def create_synthetic_test_images(temp_dir: Path) -> Dict[str, Path]:
    """Generate controlled test images for empirical forensic evaluation."""
    # 1. Pristine clean image (single compression pass)
    pristine_path = temp_dir / "pristine_landscape.jpg"
    img_pristine = Image.new("RGB", (300, 300), color=(120, 180, 220))
    draw = ImageDraw.Draw(img_pristine)
    draw.rectangle([50, 50, 250, 250], fill=(80, 150, 80))
    img_pristine.save(pristine_path, format="JPEG", quality=95)

    # 2. Spliced image (inserting an uncompressed patch into a compressed baseline)
    spliced_path = temp_dir / "spliced_tampered.jpg"
    # First save base at lower quality
    base_buf = io.BytesIO()
    img_pristine.save(base_buf, format="JPEG", quality=60)
    base_buf.seek(0)
    base_reopened = Image.open(base_buf).convert("RGB")
    # Paste a high-frequency noisy patch
    patch_arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    patch_img = Image.fromarray(patch_arr)
    base_reopened.paste(patch_img, (100, 100))
    base_reopened.save(spliced_path, format="JPEG", quality=95)

    # 3. Image with simulated EXIF Software tag
    tagged_path = temp_dir / "tagged_photoshop.jpg"
    exif = img_pristine.getexif()
    # 305 is Software tag in TIFF / EXIF standard
    exif[305] = "Adobe Photoshop 2024"
    exif[271] = "Canon"
    exif[272] = "EOS R5"
    img_pristine.save(tagged_path, format="JPEG", quality=90, exif=exif)

    # 4. Stripped image (no EXIF metadata)
    stripped_path = temp_dir / "stripped_clean.jpg"
    clean_no_exif = Image.fromarray(np.array(img_pristine))
    clean_no_exif.save(stripped_path, format="JPEG", quality=90)

    return {
        "pristine": pristine_path,
        "spliced": spliced_path,
        "tagged": tagged_path,
        "stripped": stripped_path,
    }


def forensics_benchmark_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Evaluates media forensic modules against controlled forensic sample pairs."""
    ela_analyzer = ELAForensics()
    meta_analyzer = MetadataForensics()
    synth_analyzer = HeuristicFrequencySyntheticDetector()

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        test_images = create_synthetic_test_images(tmp_dir)

        # 1. ELA Evaluation
        ela_pristine = ela_analyzer.analyze(test_images["pristine"])
        ela_spliced = ela_analyzer.analyze(test_images["spliced"])

        # 2. Metadata Evaluation
        meta_tagged = meta_analyzer.analyze(test_images["tagged"])
        meta_stripped = meta_analyzer.analyze(test_images["stripped"])

        # 3. Synthetic Media Heuristic Evaluation
        synth_pristine = synth_analyzer.analyze(test_images["pristine"])
        synth_spliced = synth_analyzer.analyze(test_images["spliced"])

    # Analyze ELA discrimination
    ela_contrast_ratio = (
        round(ela_spliced["ela_max_error"] / max(0.01, ela_pristine["ela_max_error"]), 3)
    )

    return {
        "benchmark_type": "RESEARCH_BENCHMARK",
        "description": "Evaluation of auxiliary media forensic signals on controlled test images",
        "scientific_integrity_status": {
            "exif_metadata": "AUXILIARY SIGNAL (Metadata is routinely stripped or spoofed; presence != authenticity).",
            "error_level_analysis": "AUXILIARY SIGNAL (Indicates compression rate variance; does not prove forgery).",
            "synthetic_media_heuristic": "UNVALIDATED EXPLORATORY SIGNAL (Statistical pixel variance heuristic; NOT a validated AI-image detector).",
        },
        "results": {
            "error_level_analysis": {
                "pristine_max_error": ela_pristine["ela_max_error"],
                "spliced_max_error": ela_spliced["ela_max_error"],
                "spliced_detected": ela_spliced["is_ela_spliced"],
                "ela_variance_contrast_ratio": ela_contrast_ratio,
            },
            "metadata_forensics": {
                "tagged_software_detected": meta_tagged.get("software_tag"),
                "tagged_has_exif": meta_tagged.get("has_exif"),
                "stripped_has_exif": meta_stripped.get("has_exif"),
                "c2pa_credentials_found": meta_tagged.get("c2pa_present"),
            },
            "synthetic_heuristic": {
                "pristine_score": synth_pristine.get("synthetic_probability"),
                "spliced_score": synth_spliced.get("synthetic_probability"),
                "validation_status": "EXPLICITLY_UNVALIDATED",
            },
        },
    }


def run_forensics_benchmark() -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_id="EXP-10-FORENSICS",
        name="media_forensics_benchmark",
        description="Controlled evaluation of auxiliary media forensic signals",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(forensics_benchmark_experiment)

    out_path = Path("research/results/forensics_benchmark.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    return res


if __name__ == "__main__":
    run_forensics_benchmark()
