from datetime import datetime, timezone
import re
import dateparser

PRESENT_URGENCY_MARKERS = {
    "breaking", "today", "yesterday", "right now", "happening now",
    "just in", "urgent", "immediate", "current", "this morning", "tonight"
}


class TemporalParser:
    """Parses temporal anchors, detects present-tense urgency framing, and normalizes timestamps."""

    def __init__(self):
        self.year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")

    def has_present_framing(self, text: str) -> bool:
        lower = text.lower()
        return any(marker in lower for marker in PRESENT_URGENCY_MARKERS)

    def parse_text_timestamp(self, text: str) -> tuple[str | None, datetime | None]:
        lower = text.lower()
        
        # Check year first
        years = self.year_pattern.findall(text)
        if years:
            year_str = years[0]
            parsed = dateparser.parse(f"01/01/{year_str}")
            if parsed:
                return year_str, parsed.replace(tzinfo=timezone.utc)

        # Check relative or explicit date phrases
        date_candidates = re.findall(
            r"\b(?:on\s+)?([A-Z][a-z]+\s+\d{1,2}(?:,\s+\d{4})?)\b",
            text
        )
        if date_candidates:
            phrase = date_candidates[0]
            parsed = dateparser.parse(phrase)
            if parsed:
                return phrase, parsed.replace(tzinfo=timezone.utc)

        return None, None


temporal_parser = TemporalParser()
