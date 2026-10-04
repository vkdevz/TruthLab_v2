from pathlib import Path
from PIL import Image
import re


class OCREngine:
    """Extracts text from screenshots, memes, and infographics with adaptive fallbacks."""

    def __init__(self):
        self._easyocr_reader = None

    def _get_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                # Initialize EasyOCR for English
                self._easyocr_reader = easyocr.Reader(["en"], gpu=False)
            except Exception:
                self._easyocr_reader = False
        return self._easyocr_reader

    def extract_text(self, image_path: Path | str) -> str:
        path = Path(image_path)
        if not path.exists():
            return ""

        reader = self._get_reader()
        if reader:
            try:
                results = reader.readtext(str(path), detail=0)
                extracted = " ".join(results)
                return extracted.strip()
            except Exception:
                pass

        # Fallback inspection: check if image has embedded text metadata (e.g. PNG text chunk)
        try:
            with Image.open(path) as img:
                info = img.info
                text_chunks = [str(v) for k, v in info.items() if isinstance(v, (str, bytes))]
                if text_chunks:
                    return " ".join(text_chunks).strip()
        except Exception:
            pass

        return ""


ocr_engine = OCREngine()
