import re


class SearchQueryGenerator:
    """Formulates diverse semantic and Boolean search queries from atomic claims and extracted entities."""

    def generate_queries(self, canonical_claim: str, entities: list[str], temporal_anchor: str | None = None) -> list[str]:
        queries = []

        # 1. Exact fact-check query (targeting existing debunkings or official reports)
        clean_claim = re.sub(r'[^\w\s]', '', canonical_claim).strip()
        queries.append(f"{clean_claim} fact check")

        # 2. Entity-focused query
        if entities:
            top_entities = " ".join(entities[:3])
            # Extract key action verbs or numbers from claim
            tokens = [t for t in clean_claim.split() if len(t) > 3 and t not in entities]
            key_tokens = " ".join(tokens[:3])
            queries.append(f"{top_entities} {key_tokens}")

        # 3. Temporal-grounded query
        if temporal_anchor:
            queries.append(f"{clean_claim} {temporal_anchor}")

        # 4. Strict assertion query
        queries.append(clean_claim)

        # Deduplicate
        deduped = list(dict.fromkeys([q.strip() for q in queries if q.strip()]))
        return deduped[:4]


query_generator = SearchQueryGenerator()
