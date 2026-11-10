import re
from backend.app.schemas.veracity import StanceType
from backend.app.schemas.evidence import EvidenceSnippet

CONTRADICTION_CUES = {
    "false", "fake", "incorrect", "debunked", "no evidence", "refuted",
    "denied", "hoax", "misleading", "fabricated", "unfounded", "untrue",
    "contrary", "disputed", "inaccurate", "never happened", "contradicts"
}

ENTAILMENT_CUES = {
    "confirmed", "verified", "true", "accurate", "official", "published",
    "agreed", "corroborates", "evidence shows", "substantiated", "proven",
    "announced", "authenticated"
}


class NLIEvidenceInterpreter:
    """Interprets the semantic relationship between claim and evidence passage.
    Important: NLI represents evidence interpretation, NOT absolute proof of truth."""

    def evaluate_relationship(self, claim_text: str, snippet_text: str) -> tuple[StanceType, dict[str, float]]:
        c_lower = claim_text.lower()
        s_lower = snippet_text.lower()

        refute_hits = sum(1 for cue in CONTRADICTION_CUES if cue in s_lower)
        support_hits = sum(1 for cue in ENTAILMENT_CUES if cue in s_lower)

        if refute_hits > support_hits and refute_hits >= 1:
            stance = StanceType.REFUTES
            probs = {"SUPPORTS": 0.05, "REFUTES": 0.88, "NEUTRAL": 0.07}
        elif support_hits > refute_hits and support_hits >= 1:
            stance = StanceType.SUPPORTS
            probs = {"SUPPORTS": 0.88, "REFUTES": 0.05, "NEUTRAL": 0.07}
        else:
            # Without explicit entailment or contradiction cues, topical token overlap
            # indicates relevance, NOT entailment. Default safely to NEUTRAL.
            stance = StanceType.NEUTRAL
            probs = {"SUPPORTS": 0.10, "REFUTES": 0.10, "NEUTRAL": 0.80}

        return stance, probs

    def process_evidence_stances(self, claim_text: str, evidence_items: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
        for item in evidence_items:
            # Preserve ClaimReview expert stance if already determined
            if not item.is_claim_review or item.stance == StanceType.NEUTRAL:
                stance, probs = self.evaluate_relationship(claim_text, item.snippet_text)
                item.stance = stance
                item.stance_probabilities = probs
        return evidence_items


nli_interpreter = NLIEvidenceInterpreter()
