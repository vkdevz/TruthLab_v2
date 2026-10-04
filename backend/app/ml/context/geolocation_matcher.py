import re

COMMON_LOCATIONS = {
    "us": "united states",
    "usa": "united states",
    "uk": "united kingdom",
    "india": "india",
    "delhi": "india",
    "mumbai": "india",
    "florida": "united states",
    "california": "united states",
    "texas": "united states",
    "london": "united kingdom",
    "paris": "france",
    "china": "china",
    "beijing": "china",
    "tokyo": "japan",
    "kyiv": "ukraine",
    "ukraine": "ukraine",
    "moscow": "russia",
    "russia": "russia",
    "gaza": "palestine",
    "philippines": "philippines",
    "manila": "philippines",
    "canada": "canada",
    "australia": "australia",
    "germany": "germany",
    "france": "france",
    "brazil": "brazil",
}


class GeolocationMatcher:
    """Verifies geographic consistency between claim assertions and retrieved evidence locations."""

    def extract_locations(self, text: str) -> set[str]:
        words = re.findall(r"\b[A-Za-z]+\b", text.lower())
        found = set()
        for w in words:
            if w in COMMON_LOCATIONS:
                found.add(COMMON_LOCATIONS[w])
        return found

    def check_consistency(self, claim_text: str, evidence_snippets: list[str]) -> tuple[str, list[str]]:
        claim_locs = self.extract_locations(claim_text)
        if not claim_locs:
            return "UNKNOWN", []

        all_evidence_text = " ".join(evidence_snippets)
        evidence_locs = self.extract_locations(all_evidence_text)

        if not evidence_locs:
            return "UNKNOWN", []

        # If claim specifies a location, but evidence explicitly discusses a completely different region
        common = claim_locs.intersection(evidence_locs)
        if common:
            return "CONSISTENT", [f"Geographic entity confirmed in evidence: {', '.join(common)}"]

        return "MISMATCH", [
            f"Geographic inconsistency detected: claim asserts location ({', '.join(claim_locs)}), "
            f"while retrieved evidence refers to ({', '.join(evidence_locs)})."
        ]


geolocation_matcher = GeolocationMatcher()
