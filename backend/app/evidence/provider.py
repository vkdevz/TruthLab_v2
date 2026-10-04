from abc import ABC, abstractmethod
from datetime import datetime, timezone
import hashlib
from urllib.parse import urlparse
import httpx
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType
from backend.app.core.config import settings
from backend.app.services.retrieval.factcheck_cache import REFERENCE_CLAIM_REVIEWS


class EvidenceProvider(ABC):
    """Abstract Base Class for external and local evidence sources."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the evidence provider."""
        pass

    @abstractmethod
    async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]:
        """Retrieves candidate evidence snippets matching the query."""
        pass


class LocalClaimReviewProvider(EvidenceProvider):
    """Local offline provider querying verified ClaimReview datasets/records."""

    def __init__(self, records: list[dict] | None = None):
        self.records = records or REFERENCE_CLAIM_REVIEWS

    @property
    def provider_name(self) -> str:
        return "Local ClaimReview Index"

    async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]:
        query_tokens = {w.strip(" ,.?!'\"") for w in query.lower().split() if len(w) > 2}
        results = []

        for idx, rec in enumerate(self.records):
            rec_tokens = {w.strip(" ,.?!'\"") for w in rec["claim"].lower().split() if len(w) > 2}
            intersection = query_tokens.intersection(rec_tokens)
            containment = len(intersection) / len(query_tokens) if query_tokens else 0.0
            union = query_tokens.union(rec_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0
            relevance = max(containment, jaccard)

            if relevance >= 0.20 or len(intersection) >= 2:
                stance = rec["stance"]
                probs = {
                    "SUPPORTS": 0.92 if stance == StanceType.SUPPORTS else 0.03,
                    "REFUTES": 0.92 if stance == StanceType.REFUTES else 0.03,
                    "NEUTRAL": 0.05
                }

                snippet = EvidenceSnippet(
                    id=f"loc-{idx}-{hashlib.md5(rec['url'].encode()).hexdigest()[:6]}",
                    claim_id=claim_id,
                    source_name=rec["publisher"],
                    source_url=rec["url"],
                    domain=rec["domain"],
                    domain_credibility_weight=1.6,
                    snippet_text=rec["snippet"],
                    publication_date=datetime.fromisoformat(rec["date"].replace("Z", "+00:00")),
                    retrieval_score=round(max(0.65, relevance), 3),
                    stance=stance,
                    stance_probabilities=probs,
                    is_claim_review=True,
                    claim_review_rating=rec["rating"]
                )
                results.append(snippet)

        results.sort(key=lambda s: s.retrieval_score, reverse=True)
        return results[:limit]


class GoogleFactCheckProvider(EvidenceProvider):
    """Live provider querying the official Google Fact Check Tools API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GOOGLE_FACTCHECK_API_KEY

    @property
    def provider_name(self) -> str:
        return "Google Fact Check Tools API"

    async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]:
        if not self.api_key:
            return []

        results = []
        api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {"query": query, "key": self.api_key, "pageSize": limit}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("claims", []):
                        for rev in item.get("claimReview", []):
                            pub = rev.get("publisher", {}).get("name", "Verified Fact-Checker")
                            url = rev.get("url", "")
                            domain = urlparse(url).netloc
                            rating = rev.get("textualRating", "")
                            snippet_text = f"Fact-check by {pub} on '{item.get('text', '')}': Rated '{rating}'."

                            is_false = any(w in rating.lower() for w in ["false", "pants on fire", "incorrect", "misleading"])
                            stance = StanceType.REFUTES if is_false else StanceType.SUPPORTS

                            results.append(EvidenceSnippet(
                                id=f"gfc-{hashlib.md5(url.encode()).hexdigest()[:8]}",
                                claim_id=claim_id,
                                source_name=pub,
                                source_url=url,
                                domain=domain,
                                domain_credibility_weight=1.6,
                                snippet_text=snippet_text,
                                retrieval_score=0.88,
                                stance=stance,
                                stance_probabilities={
                                    "SUPPORTS": 0.05 if is_false else 0.90,
                                    "REFUTES": 0.90 if is_false else 0.05,
                                    "NEUTRAL": 0.05
                                },
                                is_claim_review=True,
                                claim_review_rating=rating
                            ))
        except Exception:
            # Fallback gracefully
            pass

        return results[:limit]


class CompositeEvidenceRetriever:
    """Orchestrates evidence collection across all active registered providers."""

    def __init__(self, providers: list[EvidenceProvider] | None = None):
        self.providers = providers or [
            LocalClaimReviewProvider(),
            GoogleFactCheckProvider(),
        ]

    def register_provider(self, provider: EvidenceProvider):
        self.providers.append(provider)

    async def retrieve_candidate_evidence(
        self,
        claim_id: str,
        canonical_claim: str,
        search_queries: list[str],
        per_query_limit: int = 5
    ) -> list[EvidenceSnippet]:
        all_candidates: list[EvidenceSnippet] = []

        # Query all providers across generated queries
        for provider in self.providers:
            for q in search_queries:
                try:
                    items = await provider.retrieve(query=q, claim_id=claim_id, limit=per_query_limit)
                    all_candidates.extend(items)
                except Exception:
                    pass

        # Deduplicate candidates by source URL
        seen_urls = set()
        deduped = []
        for ev in all_candidates:
            if ev.source_url not in seen_urls:
                seen_urls.add(ev.source_url)
                deduped.append(ev)

        return deduped


composite_evidence_retriever = CompositeEvidenceRetriever()
