from pathlib import Path
from PIL import Image
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.image.ocr_engine import ocr_engine


class SceneExtractor:
    """Manages scene detection, key-frame extraction, and visual overlay OCR across sampled frames."""

    async def extract_and_analyze_scenes(self, video_path: Path | str, scratch_dir: Path | str) -> tuple[list[Path], str]:
        frames = await ffmpeg_processor.extract_keyframes(video_path, scratch_dir, max_frames=6)
        
        extracted_texts = []
        for frame in frames:
            text = ocr_engine.extract_text(frame)
            if text and len(text.strip()) > 4:
                extracted_texts.append(text.strip())

        # Deduplicate and combine unique text overlays
        unique_overlays = list(dict.fromkeys(extracted_texts))
        combined_ocr = " | ".join(unique_overlays)
        return frames, combined_ocr


scene_extractor = SceneExtractor()
