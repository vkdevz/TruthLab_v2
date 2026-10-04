import re
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType

CONTRADICTION_CUES = {
    "false", "fake", "incorrect", "debunked", "no evidence", "refuted",
    "denied", "hoax", "misleading", "fabricated", "unfounded", "untrue",
    "contrary", "disputed", "inaccurate", "never happened"
}

ENTTAILMENT_CUES = {
    "confirmed", "verified", "true", "accurate", "official", "published",
    "agreed", "corroborates", "evidence shows", "substantiated", "proven"
}


class StanceClassifier:
    """Predicts entailment, contradiction, or neutrality between a claim and an evidence snippet."""

    def predict_stance(self, claim_text: str, snippet_text: str) -> tuple[StanceType, dict[str, float]]:
        c_lower = claim_text.lower()
        s_lower = snippet_text.lower()

        # Check for explicit refutation markers in evidence
        refute_hits = sum(1 for cue in CONTRADICTION_CUES if cue in s_lower)
        support_hits = sum(1 for cue in ENTTAILMENT_CUES if cue in s_lower)

        if refute_hits > support_hits and refute_hits >= 1:
            stance = StanceType.REFUTES
            probs = {"SUPPORTS": 0.05, "REFUTES": 0.88, "NEUTRAL": 0.07}
        elif support_hits > refute_hits and support_hits >= 1:
            stance = StanceType.SUPPORTS
            probs = {"SUPPORTS": 0.88, "REFUTES": 0.05, "NEUTRAL": 0.07}
        else:
            # Check lexical overlap
            c_tokens = set(re.findall(r"\w+", c_lower))
            s_tokens = set(re.findall(r"\w+", s_lower))
            overlap = len(c_tokens.intersection(s_tokens))
            if overlap >= 3:
                stance = StanceType.SUPPORTS
                probs = {"SUPPORTS": 0.65, "REFUTES": 0.15, "NEUTRAL": 0.20}
            else:
                stance = StanceType.NEUTRAL
                probs = {"SUPPORTS": 0.20, "REFUTES": 0.20, "NEUTRAL": 0.60}

        return stance, probs

    def evaluate_evidence_stances(self, claim_text: str, evidence_items: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
        for item in evidence_items:
            # If already verified by ClaimReview, retain high-fidelity review stance
            if not item.is_claim_review:
                stance, probs = self.predict_stance(claim_text, item.snippet_text)
                item.stance = stance
                item.stance_probabilities = probs
        return evidence_items


stance_classifier = StanceClassifier()
