from datetime import datetime
import re
import dateparser


class EntityExtractor:
    """Extracts named entities, organizations, locations, and temporal anchors."""

    def __init__(self):
        # Common months and relative temporal markers
        self.year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")
        self.date_phrase_pattern = re.compile(
            r"\b(yesterday|today|last week|last month|in \d{4}|on [A-Z][a-z]+ \d{1,2}(?:, \d{4})?)\b",
            re.IGNORECASE
        )
        self.capitalized_entity_pattern = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")

    def extract(self, text: str) -> tuple[list[str], str | None, datetime | None]:
        # Extract named entity candidates
        matches = self.capitalized_entity_pattern.findall(text)
        # Filter out common sentence starters
        stopwords = {"The", "A", "An", "In", "On", "At", "Breaking", "According", "This", "That", "It"}
        entities = [m for m in matches if m not in stopwords and len(m) > 2]
        
        # Deduplicate while preserving order
        deduped_entities = list(dict.fromkeys(entities))

        # Extract temporal anchor
        temporal_anchor = None
        inferred_date = None

        date_match = self.date_phrase_pattern.search(text)
        if date_match:
            temporal_anchor = date_match.group(0)
            parsed = dateparser.parse(temporal_anchor)
            if parsed:
                inferred_date = parsed
        else:
            year_match = self.year_pattern.search(text)
            if year_match:
                temporal_anchor = year_match.group(0)
                parsed = dateparser.parse(f"01/01/{temporal_anchor}")
                if parsed:
                    inferred_date = parsed

        return deduped_entities, temporal_anchor, inferred_date


entity_extractor = EntityExtractor()
