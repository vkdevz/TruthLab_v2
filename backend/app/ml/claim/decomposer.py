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

    def decompose(self, text: str) -> list[AtomicClaim]:
        cleaned = text.strip()
        if not cleaned:
            return []

        # Split into preliminary clauses and sentences
        raw_segments = self.split_pattern.split(cleaned)
        claims = []

        for seg in raw_segments:
            seg_clean = seg.strip(" ,.;:-\n\t")
            if len(seg_clean.split()) < 4:
                continue

            score, is_checkworthy = checkworthiness_scorer.score(seg_clean)
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
            claims.append(claim_obj)

        return claims


claim_decomposer = ClaimDecomposer()
