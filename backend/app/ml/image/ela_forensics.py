import io
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance
import numpy as np


class ELAForensics:
    """Error Level Analysis (ELA) for detecting JPEG re-compression and splicing anomalies."""

    def analyze(self, image_path: Path | str, quality: int = 90) -> dict[str, any]:
        path = Path(image_path)
        if not path.exists():
            return {"ela_max_error": 0.0, "is_ela_spliced": False, "notes": ["File missing"]}

        notes = []

        try:
            with Image.open(path) as orig_img:
                rgb_img = orig_img.convert("RGB")
                
                # Re-save to memory buffer at standardized JPEG quality
                buffer = io.BytesIO()
                rgb_img.save(buffer, format="JPEG", quality=quality)
                buffer.seek(0)
                
                resaved_img = Image.open(buffer)

                # Compute absolute pixel difference
                diff = ImageChops.difference(rgb_img, resaved_img)
                
                # Convert to numpy array for variance analysis
                diff_arr = np.asarray(diff, dtype=np.float32)
                max_diff = float(np.max(diff_arr)) / 255.0
                mean_diff = float(np.mean(diff_arr)) / 255.0
                std_diff = float(np.std(diff_arr)) / 255.0

                # Splicing heuristic: high local error variance compared to background
                is_spliced = (std_diff > 0.08) and (max_diff > 0.35)
                
                if is_spliced:
                    notes.append(
                        f"ELA detected localized compression error variance (max: {max_diff:.2f}, std: {std_diff:.2f}), "
                        f"suggestive of digital splicing or layered editing."
                    )
                else:
                    notes.append("ELA error distribution is relatively uniform across the image plane.")

                return {
                    "ela_max_error": round(max_diff, 3),
                    "is_ela_spliced": is_spliced,
                    "notes": notes,
                }

        except Exception as exc:
            return {
                "ela_max_error": 0.0,
                "is_ela_spliced": False,
                "notes": [f"ELA processing error: {str(exc)}"],
            }


ela_forensics = ELAForensics()
