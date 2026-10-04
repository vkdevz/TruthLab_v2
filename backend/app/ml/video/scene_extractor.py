from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.image.ocr_engine import ocr_engine
from backend.app.ml.image.ela_forensics import ela_forensics
from backend.app.ml.image.synthetic_detector import synthetic_detector


class SceneExtractor:
    """Manages scene detection, key-frame extraction, and visual overlay OCR across sampled frames,
    preserving frame timestamps, bounding regions, and frame-level visual forensic indicators."""

    async def extract_and_analyze_scenes(
        self, video_path: Path | str, scratch_dir: Path | str
    ) -> tuple[list[Path], str, list[dict[str, Any]]]:
        """Extracts keyframes, executes OCR and visual forensics on each, returning:
        (frames_list, combined_ocr_text, detailed_frame_findings)."""
        frame_records = await ffmpeg_processor.extract_keyframes_with_timestamps(
            video_path, scratch_dir, max_frames=6, interval_seconds=4.0
        )

        frames = []
        extracted_texts = []
        detailed_findings = []

        for rec in frame_records:
            f_path = rec["frame_path"]
            ts = rec["timestamp_seconds"]
            frames.append(f_path)

            # 1. OCR with confidence and bounding boxes
            ocr_res = ocr_engine.extract_ocr(f_path)
            clean_text = ocr_res.get("text", "").strip()

            if clean_text and len(clean_text) > 4:
                extracted_texts.append(clean_text)

            # 2. Keyframe visual forensic signals
            ela_res = ela_forensics.analyze(f_path)
            synth_res = synthetic_detector.analyze(f_path)

            detailed_findings.append({
                "frame_path": str(f_path),
                "timestamp_seconds": ts,
                "ocr_text": clean_text,
                "ocr_confidence": ocr_res.get("confidence", 0.0),
                "ocr_regions": ocr_res.get("regions", []),
                "ela_max_error": ela_res.get("ela_max_error", 0.0),
                "is_ela_spliced": ela_res.get("is_ela_spliced", False),
                "synthetic_probability": synth_res.get("synthetic_probability", 0.15),
            })

        # Deduplicate and combine unique text overlays
        unique_overlays = list(dict.fromkeys(extracted_texts))
        combined_ocr = " | ".join(unique_overlays)

        return frames, combined_ocr, detailed_findings


scene_extractor = SceneExtractor()

