import re
import uuid
from backend.app.schemas.claim import AtomicClaim
from backend.app.ml.claim.checkworthiness import checkworthiness_scorer
from backend.app.ml.claim.entity_extractor import entity_extractor
from backend.app.ml.claim.query_generator import query_generator


class ClaimDecomposer:
    """Decomposes compound sentences and text bodies into atomic, check-worthy factual propositions."""

    def __init__(self):
        # Conjunction splitting patterns
        self.split_pattern = re.compile(r"(?<=[.!?])\s+|(?<=[,;])\s+(?:and|but|while|whereas|moreover|furthermore)\s+", re.IGNORECASE)

    def _clean_article_text(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            line_str = line.strip()
            # Skip markdown table rows, dividers, headers, gallery/edit tags
            if not line_str or line_str.startswith("|") or line_str.endswith("|") or line_str.startswith("#"):
                continue
            if "[edit]" in line_str.lower() or line_str.lower().startswith("gallery") or line_str.lower().startswith("references"):
                continue
            if re.match(r"^[-=_*]{3,}$", line_str):
                continue
            # Remove inline footnote references e.g. [1], [23]
            clean_line = re.sub(r"\[\d+\]", "", line_str)
            lines.append(clean_line)
        return " ".join(lines)

    def decompose(self, text: str, max_claims: int = 5) -> list[AtomicClaim]:
        cleaned = self._clean_article_text(text)
        if not cleaned:
            return []

        # Split into preliminary clauses and sentences
        raw_segments = self.split_pattern.split(cleaned)
        candidate_claims = []

        for seg in raw_segments:
            seg_clean = seg.strip(" ,.;:-\n\t\"'")
            # Require minimum length and sentence structure
            words = seg_clean.split()
            if len(words) < 4 or "|" in seg_clean:
                continue

            # Must contain letters
            if not re.search(r"[a-zA-Z]", seg_clean):
                continue

            score, is_checkworthy = checkworthiness_scorer.score(seg_clean)
            if not is_checkworthy and score < 0.50:
                continue

            entities, temporal_anchor, inferred_date = entity_extractor.extract(seg_clean)

            # Generate query variations for evidence retrieval
            search_queries = query_generator.generate_queries(
                canonical_claim=seg_clean,
                entities=entities,
                temporal_anchor=temporal_anchor
            )

            claim_obj = AtomicClaim(
                id=f"c-{uuid.uuid4().hex[:8]}",
                raw_text=seg_clean,
                canonical_claim=seg_clean,
                checkworthy_score=score,
                is_checkworthy=is_checkworthy,
                entities=entities,
                temporal_anchor=temporal_anchor,
                inferred_date=inferred_date,
                search_queries=search_queries,
            )
            candidate_claims.append(claim_obj)

        # Prioritize most checkworthy claims up to max_claims
        candidate_claims.sort(key=lambda c: c.checkworthy_score, reverse=True)
        return candidate_claims[:max_claims]


claim_decomposer = ClaimDecomposer()
