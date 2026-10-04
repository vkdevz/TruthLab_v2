import re
import unicodedata
from fastapi import HTTPException
from backend.app.core.config import settings


class TextIngestionService:
    """Normalizes and sanitizes raw textual submissions."""

    MIN_TEXT_CHARS = 5
    MAX_TEXT_CHARS = 25_000

    def ingest_text(self, text: str) -> str:
        if not text or not isinstance(text, str):
            raise HTTPException(status_code=400, detail="Text submission must be a non-empty string.")

        # Unicode normalization (NFKC decomposes compatibility characters cleanly)
        normalized = unicodedata.normalize("NFKC", text)

        # Normalize multiple spaces, tabs, and line breaks
        cleaned = re.sub(r"[ \t]+", " ", normalized)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned).strip()

        if len(cleaned) < self.MIN_TEXT_CHARS:
            raise HTTPException(
                status_code=400,
                detail=f"Submitted text is too short. Minimum {self.MIN_TEXT_CHARS} characters required."
            )

        if len(cleaned) > self.MAX_TEXT_CHARS:
            raise HTTPException(
                status_code=413,
                detail=f"Submitted text exceeds maximum length of {self.MAX_TEXT_CHARS} characters."
            )

        return cleaned


text_ingestion_service = TextIngestionService()
