from pathlib import Path
from PIL import Image
import re
from typing import Any, Dict, List


class OCREngine:
    """Extracts text from screenshots, memes, posters, and photographs with bounding regions,
    confidence metrics, and text normalization suitable for claim extraction."""

    def __init__(self, primary_language: str = "en"):
        self.primary_language = primary_language
        self._easyocr_reader = None

    def _get_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader([self.primary_language], gpu=False)
            except Exception:
                self._easyocr_reader = False
        return self._easyocr_reader

    def normalize_ocr_text(self, text: str) -> str:
        """Normalizes noisy OCR text: cleans spurious symbols, merges broken words and whitespace."""
        if not text:
            return ""
        # Remove unprintable / non-ascii artifacts while preserving normal punctuation
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)
        # Collapse multiple spaces or tabs
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        # Fix spaced-out words (e.g., "B R E A K I N G" -> "BREAKING")
        cleaned = re.sub(r"(?<=\b[A-Za-z])\s+(?=[A-Za-z]\b)", "", cleaned)
        # Clean excessive newlines
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
        return cleaned.strip()


    def extract_ocr(self, image_path: Path | str) -> dict[str, Any]:
        """Returns structured OCR payload: text, confidence, and bounding regions."""
        path = Path(image_path)
        if not path.exists():
            return {"text": "", "confidence": 0.0, "regions": []}

        # 1. Try EasyOCR if available
        reader = self._get_reader()
        if reader:
            try:
                raw_results = reader.readtext(str(path))
                # EasyOCR returns list of (bbox, text, conf)
                extracted_lines = []
                regions = []
                confs = []

                for item in raw_results:
                    if len(item) >= 3:
                        bbox, txt, conf = item[0], item[1], float(item[2])
                        clean_txt = self.normalize_ocr_text(txt)
                        if clean_txt:
                            extracted_lines.append(clean_txt)
                            confs.append(conf)
                            regions.append({
                                "text": clean_txt,
                                "confidence": round(conf, 3),
                                "bounding_box": bbox,
                            })

                combined_text = " ".join(extracted_lines).strip()
                avg_conf = float(round(sum(confs) / len(confs), 3)) if confs else 0.0
                return {
                    "text": self.normalize_ocr_text(combined_text),
                    "confidence": avg_conf,
                    "regions": regions,
                }
            except Exception:
                pass

        # 2. Try pytesseract if available in environment
        try:
            import pytesseract
            data = pytesseract.image_to_data(Image.open(path), output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            lines = []
            regions = []
            confs = []
            for i in range(n_boxes):
                word = data["text"][i].strip()
                conf_val = float(data["conf"][i])
                if word and conf_val > 0:
                    lines.append(word)
                    confs.append(conf_val / 100.0)
                    regions.append({
                        "text": word,
                        "confidence": round(conf_val / 100.0, 3),
                        "bounding_box": [
                            data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                        ],
                    })

            if lines:
                text_out = " ".join(lines)
                avg_c = float(round(sum(confs) / len(confs), 3)) if confs else 0.0
                return {
                    "text": self.normalize_ocr_text(text_out),
                    "confidence": avg_c,
                    "regions": regions,
                }
        except Exception:
            pass

        # 3. Fallback: inspect image metadata text chunks (PNG info, EXIF comment)
        try:
            with Image.open(path) as img:
                info = img.info
                text_chunks = []
                for k, v in info.items():
                    val = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
                    val = val.strip()
                    # Filter out technical encoding signatures and require meaningful comment/description keys
                    if len(val) > 5 and not any(sig in val.lower() for sig in ["lavc", "lavf", "ffmpeg", "libx264", "encoder"]):
                        if any(meta_k in str(k).lower() for meta_k in ["comment", "description", "caption", "title", "text"]):
                            text_chunks.append(val)
                if text_chunks:
                    meta_text = " ".join(text_chunks)
                    clean = self.normalize_ocr_text(meta_text)
                    if clean:
                        return {
                            "text": clean,
                            "confidence": 0.85,
                            "regions": [{"text": clean, "confidence": 0.85, "bounding_box": None}],
                        }
        except Exception:
            pass

        return {"text": "", "confidence": 0.0, "regions": []}

    def extract_text(self, image_path: Path | str) -> str:
        """Backward-compatible helper returning cleaned extracted string."""
        ocr_res = self.extract_ocr(image_path)
        return ocr_res.get("text", "")


ocr_engine = OCREngine()

