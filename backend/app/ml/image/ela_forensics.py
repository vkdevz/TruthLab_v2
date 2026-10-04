import io
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np
from typing import Any, Dict


class ELAForensics:
    """Error Level Analysis (ELA) and compression statistics for detecting localized re-compression anomalies.
    Emits a calibrated manipulation signal and explicitly disclaims that ELA alone does not prove forgery."""

    def analyze(self, image_path: Path | str, quality: int = 90) -> dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            return {
                "ela_max_error": 0.0,
                "is_ela_spliced": False,
                "manipulation_signal": {
                    "score": 0.0,
                    "interpretation": "File not found",
                    "limitations": "Input image could not be located.",
                },
                "image_statistics": {},
                "notes": ["File missing"],
            }

        notes = []

        try:
            with Image.open(path) as orig_img:
                width, height = orig_img.size
                aspect_ratio = round(width / max(1, height), 3)
                rgb_img = orig_img.convert("RGB")

                # Re-save to memory buffer at standardized JPEG quality
                buffer = io.BytesIO()
                rgb_img.save(buffer, format="JPEG", quality=quality)
                buffer.seek(0)

                resaved_img = Image.open(buffer)

                # Compute absolute pixel difference across channels
                diff = ImageChops.difference(rgb_img, resaved_img)

                # Convert to numpy array for variance & compression analysis
                diff_arr = np.asarray(diff, dtype=np.float32)
                max_diff = float(np.max(diff_arr)) / 255.0
                mean_diff = float(np.mean(diff_arr)) / 255.0
                std_diff = float(np.std(diff_arr)) / 255.0

                # Analyze regional block variance (8x8 JPEG grid)
                h, w, _ = diff_arr.shape
                block_size = 16
                high_error_blocks = 0
                total_blocks = max(1, (h // block_size) * (w // block_size))

                for y in range(0, h - block_size + 1, block_size):
                    for x in range(0, w - block_size + 1, block_size):
                        block = diff_arr[y : y + block_size, x : x + block_size]
                        if np.mean(block) / 255.0 > (mean_diff * 2.5 + 0.05):
                            high_error_blocks += 1

                unusual_region_ratio = round(high_error_blocks / total_blocks, 4)

                # Compute a continuous manipulation risk score [0.0, 1.0]
                # High max diff + high variance + high localized anomaly ratio
                raw_score = (std_diff * 4.0) + (max_diff * 0.4) + (unusual_region_ratio * 0.8)
                manip_score = float(round(max(0.0, min(1.0, raw_score)), 3))

                is_spliced = (std_diff > 0.08 and max_diff > 0.35) or (unusual_region_ratio > 0.15 and max_diff > 0.30)

                if is_spliced:
                    interpretation = (
                        f"Non-uniform error distribution detected (variance std: {std_diff:.3f}, max error: {max_diff:.3f}, "
                        f"anomalous blocks: {unusual_region_ratio*100:.1f}%). Suggestive of composite insertion or selective re-saving."
                    )
                    notes.append(interpretation)
                else:
                    interpretation = "Error levels are relatively uniform across the image plane, consistent with uniform single-pass compression."
                    notes.append(interpretation)

                limitations = (
                    "ELA is a qualitative compression heuristic. Results are influenced by resaving quality, social media re-encoding, "
                    "uniform textures, and high contrast edges. ELA does NOT constitute definitive proof of forgery."
                )

                image_stats = {
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "mean_error": round(mean_diff, 4),
                    "std_error": round(std_diff, 4),
                    "max_error": round(max_diff, 4),
                    "anomalous_block_ratio": unusual_region_ratio,
                }

                manipulation_signal = {
                    "score": manip_score,
                    "interpretation": interpretation,
                    "limitations": limitations,
                }

                return {
                    "ela_max_error": round(max_diff, 3),
                    "is_ela_spliced": is_spliced,
                    "manipulation_signal": manipulation_signal,
                    "image_statistics": image_stats,
                    "notes": notes,
                }

        except Exception as exc:
            return {
                "ela_max_error": 0.0,
                "is_ela_spliced": False,
                "manipulation_signal": {
                    "score": 0.0,
                    "interpretation": f"ELA processing error: {str(exc)}",
                    "limitations": "Processing failed.",
                },
                "image_statistics": {},
                "notes": [f"ELA processing error: {str(exc)}"],
            }


ela_forensics = ELAForensics()

