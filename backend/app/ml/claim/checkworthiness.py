import re

OPINION_MARKERS = {
    "i think", "i believe", "in my opinion", "i feel", "to me", "personally",
    "seems like", "maybe", "probably", "perhaps", "i guess", "who knows",
    "what if", "could it be", "awesome", "terrible", "beautiful", "ugly",
    "delicious", "boring", "exciting", "masterpiece", "overrated"
}

FACTUAL_INDICATORS = {
    "announced", "confirmed", "reported", "discovered", "approved", "banned",
    "increased", "decreased", "passed", "signed", "resigned", "elected",
    "tested", "published", "launched", "stated", "decided", "claimed"
}


class CheckworthinessScorer:
    """Evaluates whether an utterance is an empirical, check-worthy factual claim
    rather than a subjective opinion, rhetorical question, or greeting."""

    def score(self, text: str) -> tuple[float, bool]:
        cleaned = text.strip()
        lower = cleaned.lower()

        # Questions and commands are generally non-checkworthy
        if cleaned.endswith("?") or lower.startswith(("why", "how", "what if", "is it true that")):
            return 0.15, False

        # Exclamations of pure sentiment
        if len(cleaned.split()) < 4:
            return 0.20, False

        score = 0.50

        # Penalize subjective opinion cues
        opinion_matches = sum(1 for m in OPINION_MARKERS if m in lower)
        score -= 0.15 * min(opinion_matches, 3)

        # Reward factual verbs
        factual_matches = sum(1 for v in FACTUAL_INDICATORS if v in lower)
        score += 0.12 * min(factual_matches, 3)

        # Reward presence of numbers, percentages, dates, or currency symbols
        if re.search(r"\b\d+(\.\d+)?%?\b|[$€£₹]", cleaned):
            score += 0.15

        # Reward proper nouns / capitalized entity clusters
        capitalized_words = re.findall(r"\b[A-Z][a-z]+\b", cleaned)
        if len(capitalized_words) >= 2:
            score += 0.10

        clamped = max(0.05, min(0.98, score))
        is_checkworthy = clamped >= 0.60
        return round(clamped, 3), is_checkworthy


checkworthiness_scorer = CheckworthinessScorer()
